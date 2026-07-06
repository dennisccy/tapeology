# goal-structure_ui-iter-0 Dev Handoff

**Phase:** goal-structure_ui-iter-0
**Date:** 2026-07-07
**Agent:** developer
**Status:** complete

## What Was Built

Nothing — by design. This is the "Structure, made visible" UI-surfacing interlude's **verify-only
baseline** (Mode: baseline, Depth: lean). The developer step is an explicit no-op per the spec's
BACKGROUND section; the entire scope was executing the spec's verification checklist against the
current codebase and a live backend/frontend, and recording the evidence below.

`git status --short` and `git diff --stat -- apps/` both confirm **zero source files changed**:

```
?? docs/phases/goal-structure_ui-iter-0.md
?? runs/goal-session-structure_ui/
```

Both untracked entries are pipeline artifacts (the iter spec doc and the goal-mode session state
directory), not product source — `git diff --stat -- apps/` returns empty. No file under `apps/`
was created, modified, or deleted this iteration.

## Baseline test counts (the J-04 sentinel anchor)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

- **Collected: 1146 items. Result: 1145 passed, 1 skipped, 2 warnings in 364.03s (0:06:04). Exit 0.**
- The single skip is `tests/test_live_integration.py:37` — `"gated: set
  TAPEOLOGY_LIVE_INTEGRATION=1 to run the real live-socket check"`. This is an explicit two-stage
  opt-in gate (env var first, then credentials, then market-hours), not a credentials-missing
  failure — expected and honest for an autonomous, keyless run.
- This is up from era-4's own closing baseline (1040 passed / 1041 collected, recorded in
  `docs/handoffs/goal-tape_to_profit_support_resistence-iter-0-dev.md` and grown across that
  session's iterations 1–6), reflecting the bars/levels/strategies/backtests/meta-routes test
  growth era 4 shipped. **The structure_ui interlude's opening baseline is 1145 passing / 1146
  collected.**

Engine equivalence tests (byte-identical outputs guard):

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py -v`

- **22 passed in 0.79s** (7 from `test_observer_equivalence.py` — the J-68 engine
  observer-seam byte-identity guard; 15 from `test_profile_equivalence.py` — the profile-registry
  byte-identity guard). Both equivalence suites are green; the frozen `default` behavior is intact.

`config_fingerprint` (live-computed, not just grepped):

```
cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"
-> 4d665603569b9dbf
```

Matches the goal.md-pinned value **exactly**.

## Journey-by-journey verification evidence

The goal-evaluator assigns pass/fail/partial statuses; this section records what the codebase and
a live backend/frontend actually showed. The spec's baseline predictions (J-01–J-03 absent, J-04
intact) were **confirmed on every point**.

### J-01 — Structure tab renders S/R levels + A/B/C confluence zones (expected FAIL) — CONFIRMED ABSENT

- `apps/frontend/app/` listing: `globals.css`, `journal/`, `layout.tsx`, `page.tsx`,
  `performance/`, `studies/` — **no `structure/` directory**. `find apps/frontend/app
  -iname "*structure*"` → zero matches.
- Live probe (frontend running on :3000): `GET /structure` → **404** (Next.js has no such route).
- `apps/backend/app/meta.py` `UI_ROUTES` (read, unchanged) carries exactly the five pre-interlude
  entries — `/` (Cockpit), `/journal` (Journal), `/journal/[id]` (non-nav detail), `/studies`
  (Studies), `/performance` (Performance) — no `/structure` entry. Live probe: `GET
  /meta/ui-routes` returns exactly that same five-entry list, byte-identical to the source.
- The underlying data the future page will read is, however, **already live** on the backend (this
  is the whole premise of the interlude — era 4 built the computation, not the view):
  `GET /research/levels?symbol=SIM-BUYER&as_of=...` → 200, `GET /research/bars` → 200. So J-01's
  gap today is purely the missing frontend route + nav entry, not missing data.

### J-02 — strategy registry and champion are visible (expected FAIL) — CONFIRMED ABSENT (data ready)

- No `/structure` page exists to render it (same absence as J-01).
- Live probe: `GET /research/strategies` → 200, returning both `v1` and `structure_tape` with full
  entry/exit/fee/slippage config (`structure_tape`'s class-scaled fields included) — the registry
  itself is complete and correct on the backend.
- Live probe: `GET /research/profiles` → 200 — `"champion":{"strategy_id":"v1","profile":"default"}`,
  `"profiles":[{"id":"default","frozen":true,"is_default":true},
  {"id":"candidate-faster-warmup","frozen":false,"is_default":false,...}]`. This is the exact
  champion-pointer state a later iteration's registry view must badge and must not move.

### J-03 — `structure_tape`-vs-`v1` comparison, honest (expected FAIL) — CONFIRMED ABSENT (job path ready)

- No `/structure` page exists to render the comparison (same absence as J-01/J-02).
- Live probe: `GET /research/datasets` → 200, `GET /research/pnl/ledger` → 200 — both endpoints the
  future comparison view will read (dataset picker, founding baseline row) are live and correct.
  Running an actual `structure_tape`-vs-`v1` backtest pair was **not** performed this iteration —
  out of scope for a verify-only baseline with no UI to drive it from; a later iteration's dev/QA
  step will exercise `POST /research/backtests` once the page exists.

### J-04 — foundation unchanged (regression sentinel) — CONFIRMED INTACT

- Full suite green (1145/1146 above); equivalence suites green (22/22 above); `config_fingerprint`
  confirmed **live-computed** as `4d665603569b9dbf`, matching the pinned value.
- Champion pointer confirmed untouched: `v1` / `default` (above).
- Live backend (`bash scripts/dev.sh`, `CHAIN_BACKEND_PORT=8000 CHAIN_FRONTEND_PORT=3000`,
  real dev DB — see "No side effects" note below):
  - `GET /health` → `{"status":"ok"}`.
  - `POST /watch/SIM-BUYER` → `{"status":"watching"}`; after 4s, `GET /tape/SIM-BUYER/state` →
    `"tape_state":"buyer_control"`, `"warm":true`, confidence ≈0.855, `"stream_status":"live"`.
    `DELETE /watch/SIM-BUYER` → `{"status":"stopped"}`.
  - `POST /watch/SIM-SELLER` → `{"status":"watching"}`; after 4s, `GET /tape/SIM-SELLER/state` →
    `"tape_state":"seller_control"`, `"warm":true`, confidence ≈0.855. `DELETE /watch/SIM-SELLER` →
    `{"status":"stopped"}`.
  - `GET /meta/ui-routes` → exactly 5 entries (4 nav + 1 non-nav detail), unchanged, no
    `/structure` entry — confirms the nav's single source of truth is untouched.
- Live frontend (`next dev`, port 3000, `NEXT_PUBLIC_API_URL=http://localhost:8000`): `GET /` → 200,
  `GET /journal` → 200, `GET /studies` → 200, `GET /performance` → 200. `GET /structure` → 404
  (expected — confirms the interlude has not started building yet).
- Backend diff confirmed as **zero** (not merely "additive nav entry only" — this iteration makes
  no backend edit at all): `git diff --stat -- apps/backend` is empty; `config.py`,
  `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the engine, and
  `app/meta.py` are all untouched.

## Files Changed

- (none — verify-only baseline; zero source modifications under `apps/`)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **1145 passed, 1 skipped** (1146 collected), 2 warnings, 364.03s, exit 0

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py -v`
Result: **22 passed** in 0.79s

## Service startup verification

- `bash scripts/dev.sh` (with `CHAIN_BACKEND_PORT=8000 CHAIN_FRONTEND_PORT=3000` to pin the
  goal.md-documented ports) started both services clean: backend `/health` → 200 within 2s,
  frontend `Ready in 1215ms`, `GET /` → 200.
- Stopped both (port-based kill, mirroring `dev.sh`'s own cleanup logic: `lsof -ti :$PORT` +
  `fuser -k -9 $PORT/tcp`, which correctly reaches the `uvicorn --reload` worker child, not just
  the reloader parent), confirmed both ports fully released, then **started dev.sh again on the
  same ports** — backend `/health` → 200 after 2s, frontend `Ready in 1190ms`, `GET /` → 200 — no
  port conflict on restart. Stopped again; final check confirms ports 8000/3000 fully released and
  no orphaned `uvicorn`/`next` process remains for this repo (an unrelated project's dev servers on
  different ports were left untouched, confirmed by PID/command-line inspection before and after).

## No side effects (baseline hygiene)

- The live smoke test above used the **real dev `TAPEOLOGY_JOURNAL_DB`** (this iteration did not
  override it with a scratch path, unlike the era-4 baseline's practice). Verified this caused no
  actual mutation: `apps/backend/journal.db`, `apps/backend/tapeology_journal.db`, and
  `journal.db-wal` all carry mtimes from **before** this iteration (2026-07-03 / 2026-07-06); none
  changed during today's test window. This is consistent with `POST /watch/{ticker}` /
  `DELETE /watch/{ticker}` being pure in-memory tape-engine operations that write no journal/thesis
  record — only `POST /research/thesis` would persist, and this iteration never called it. Noted
  here for transparency rather than silently assumed; a future iteration doing anything
  journal-writing should use a scratch DB path as era 4 did.

## Known Issues

- **Environment drift (carried over from era 3/4):** the backend venv runs Python **3.14.4** while
  `.claude/project-template.md`'s placeholder text and goal.md's Constraints section both say
  Python 3.12. The full suite is green on 3.14.4 — a documentation/environment drift observation,
  not a failure. No action taken (out of scope for a verify-only iteration).
- **`.claude/project-template.md` is still the generic unfilled template** (placeholders like
  `<e.g., Python 3.12>` throughout). README.md carries an explicit TODO flagging this ("likely
  reset by a recent incredible_auto_dev framework sync") and documents the actual verified
  commands; this developer used goal.md's Constraints section + the README's "How to run" section
  as the real stack-configuration source, matching what the era-4 baseline iteration did. Not this
  iteration's scope to fix.
- `tests/test_live_integration.py` skips on the explicit `TAPEOLOGY_LIVE_INTEGRATION=1` opt-in gate
  (expected — keyless, off-hours-safe by design).
- J-03's actual `structure_tape`-vs-`v1` backtest run was **not exercised** this iteration (no UI
  exists yet to drive it from, and the spec scopes this iteration to verification only, not to
  invoking write-side research jobs speculatively). The underlying job endpoints
  (`POST /research/backtests`, `GET /research/backtests/{id}`) were confirmed reachable
  (`GET /research/datasets` and `GET /research/pnl/ledger` both 200) but not exercised end-to-end;
  a later iteration's dev/QA step building J-03's UI will be the first to run that job pair.
- Full click-through browser verification of J-01/J-02/J-03 (confirming the *absence* renders no
  broken nav link, no client error) and J-04 (hydrated nav, cockpit panels over WebSocket, journal/
  studies/performance page content) is the browser-qa-agent's step per the spec's TESTING
  REQUIREMENTS; the evidence above is the dev-level code/API/SSR inspection leg only.

## Suggested Next Phase

Per the spec's NOTES and goal.md's dependency order (J-01 → J-02 → J-03, J-04 guarding
continuously): iteration 1 should build **J-01** — the `/structure` route
(`apps/frontend/app/structure/page.tsx`, following the `/performance` page pattern) plus the
additive `{"path": "/structure", "label": "Structure", "nav": true}` entry in `apps/backend/app/
meta.py` `UI_ROUTES`. This is the shared page home and nav unblocker for J-02 and J-03, which per
the blueprint (`runs/goal-session-structure_ui/state/blueprint.md`) are sections of the same single
page, not separate routes.
