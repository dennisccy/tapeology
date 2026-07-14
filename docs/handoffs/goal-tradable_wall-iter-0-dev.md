# goal-tradable_wall-iter-0 Dev Handoff

**Phase:** goal-tradable_wall-iter-0
**Date:** 2026-07-14
**Agent:** developer
**Status:** complete

## What Was Built

Nothing — by design. This is Era 5B "The Tradable Wall"'s **verify-only baseline** (Mode: baseline,
Depth: lean). The spec's BACKGROUND section states the developer step is an explicit no-op; the
entire scope was executing the spec's verification checklist against the current codebase and a
live backend/frontend, and recording the evidence below so the goal-evaluator can mark
`already_passing` vs. to-build for each of J-01–J-07.

`git status --short -- apps/` and `git diff --stat -- apps/` both confirm **zero source files
changed**:

```
$ git status --short -- apps/
(empty)
$ git diff --stat -- apps/
(empty)
```

Full repo status shows only pre-existing, non-`apps/` artifacts from the goal-authoring/decompose
steps that ran before this developer step (not my doing): `docs/goal.md` (modified by `/goal-init`
authoring Era 5B), `docs/goal-archive/goal-2026-07-14.md` (archived era-5 goal), the iter-0 spec
itself, and `runs/goal-session-tradable_wall/` (session state). No file under `apps/` was created,
modified, or deleted this iteration.

## Baseline test counts (the J-07 sentinel anchor)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

- **1201 passed, 6 skipped, 2 warnings in 366.28s (0:06:06). Exit 0.** (1207 collected.)
- This is **byte-identical** to Era 5's closing baseline (`docs/handoffs/goal-yahoo_fetch-iter-8-dev.md`:
  "1207 collected/1201 passed/6 skipped/0 failed"). Zero test-count drift across the era boundary —
  the goal.md rewrite that opened Era 5B touched no code under `apps/`, exactly as its own
  Constraints section requires. **The Era 5B opening baseline is 1201 passing / 1207 collected / 6
  skipped.**
- Skips: `tests/test_live_integration.py` (1, the explicit `TAPEOLOGY_LIVE_INTEGRATION=1` two-stage
  opt-in gate) + `tests/test_yahoo_live_integration.py` (5, the equivalent live-network opt-in gate
  for the Yahoo adapter) — both expected and honest for an autonomous, keyless run; neither is a
  credentials-missing failure.

Equivalence tests (byte-identical-output guard), extracted from the SAME full-suite run above (no
separate invocation needed):

- `tests/test_observer_equivalence.py` — **7/7 passed** (engine observer-seam byte-identity guard).
- `tests/test_profile_equivalence.py` — **15/15 passed** (profile-registry byte-identity guard).
- **22/22 total.** Both equivalence suites are green; the frozen `default` behavior is intact.

`config_fingerprint` (live-computed, not just grepped):

```
cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"
-> 4d665603569b9dbf
```

Matches the goal.md-pinned value **exactly**.

## Endpoint probes — Era 5B surfaces (live backend on scratch port :8301)

| Endpoint | Expected | Observed |
|---|---|---|
| `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T13:30:00Z` | 404/absent | **HTTP 404** `{"detail":"Not Found"}` |
| `GET /research/setups` | 404/absent | **HTTP 404** `{"detail":"Not Found"}` |
| `GET /research/setups/fake-id-123` | 404/absent | **HTTP 404** `{"detail":"Not Found"}` |
| `GET /research/edge-report` | 404/absent | **HTTP 404** `{"detail":"Not Found"}` |

Static confirmation (matches the live probes): `grep -n '@router\.\(get\|post\)(' apps/backend/app/research/routes.py`
lists all 29 registered routes — no `/tradability`, `/setups`, or `/edge-report` among them.
`apps/backend/app/mcp/__init__.py`'s route map (`journal`, `analytics`, `studies`, `datasets`,
`bars`, `backtests`, `strategies`, `pnl_ledger`, `taxonomy`, …) has no `tradability`/`setups`/
`edge_report` entries — the three new MCP proxies do not exist yet either.

`find apps/backend/app/research -iname "tradability.py" -o -iname "setups.py"` → no matches (both
absent). `apps/backend/app/research/edge_report.py` **does exist** (12,629 bytes) but only as the
era-3 champion-ONLY CLI (`python -m app.research.edge_report`) — no route registers it; this matches
the spec's NOTES heads-up exactly (the future J-04 builder extends this file additively rather than
forking a second computation).

## Journey-by-journey verification evidence

The goal-evaluator assigns pass/fail/partial/blocked statuses; this section records what the
codebase and a live backend/frontend actually showed. The spec's baseline predictions (J-01/J-02/
J-04/J-05/J-06 absent, J-07 intact, J-03/J-06 credential-blocked) were **confirmed on every point**.

### J-01 — The tradable level map (expected FAIL) — CONFIRMED ABSENT

- `tradability.py` absent; `GET /research/tradability` → 404 (table above); MCP `tradability` proxy
  absent.
- The raw computation it must distill is confirmed present and exactly matches the goal's Vision
  numbers: live probe `GET /research/levels?symbol=AAPL&as_of=2026-06-22T13:30:00Z` →
  **`levels: 1800`, `confluence_zones: 212`, `no_bar_series_for_symbol: false`** — byte-exact match
  to goal.md's cited "1,800 levels and 212 confluence zones" noise baseline. `research/levels.py` is
  present, unchanged, and already produces this real output on real Yahoo-fetched AAPL bars (`GET
  /research/bars?symbol=AAPL&timeframe=1d` → 6 stored series) — J-01 has real data to consume from
  day one.

### J-02 — The wide scan / case-study registry (expected FAIL) — CONFIRMED ABSENT

- `setups.py` absent; `GET /research/setups` and `GET /research/setups/{id}` → 404 (table above); MCP
  `setups` proxy absent.
- This iteration did not enumerate 5m-bar coverage across the full 12-symbol panel (out of scope for
  a code/absence-focused baseline probe) — the future J-02 builder should confirm panel bar coverage
  as its own first step per the spec's J-02 Steps 1.

### J-03 — Real tape at the wall — credentialed recording — BLOCKED (not simulated)

- Read-only presence check of the Alpaca adapter's own env vars (`apps/backend/app/providers/adapters/alpaca.py`
  defines `ENV_API_KEY = "ALPACA_API_KEY"`, `ENV_API_SECRET = "ALPACA_API_SECRET"`,
  `ENV_FEED = "ALPACA_FEED"`): **`ALPACA_API_KEY` NOT SET, `ALPACA_API_SECRET` NOT SET, `ALPACA_FEED`
  NOT SET** in this environment. No value was read or echoed — presence only.
- Per the spec's NOTES and goal.md's Constraints ("Operator act required... without them those
  journeys honestly report blocked — never simulated"), J-03 is recorded **`blocked`**, not
  attempted, not simulated. No dataset was created, no Alpaca network call was made.
- Existing infrastructure J-03 will reuse is confirmed present and untouched: `GET
  /research/datasets` → HTTP 200 (existing `DatasetStore`, empty); `GET /tape/SIM-BUYER/history` →
  HTTP 404 with the honest "not being watched" reason (`main.py:531-550`'s `_engine_or_404` — correct
  frozen behavior for an unwatched ticker, not a missing-route regression); no committed tick-fixture
  slice exists yet under `apps/backend/tests/fixtures/` (expected — that's this journey's own
  deliverable).

### J-04 — The edge report (expected FAIL) — CONFIRMED ABSENT

- `GET /research/edge-report` → 404 (table above); MCP `edge_report` proxy absent.
- `GET /research/strategies` live probe confirms exactly **two** registered strategies — `v1` and
  `structure_tape`, full config intact (entries/exits/fees/slippage/class-scaled stops+rewards) — **no
  `structure_tape_map`** entry exists yet. `edge_report.py` exists only as the era-3 CLI (see Endpoint
  probes section above) — no `BacktestJobManager`-backed 3-way report path exists.

### J-05 — `/structure` decluttered (expected FAIL, era-5 substrate intact) — CONFIRMED ABSENT

- Live frontend probe (`:3301`): `GET /structure` → HTTP 200. Raw HTML grepped for Era 5B markers:
  **no** "Tradable Map", "Case Studies", or "Edge Report" text anywhere on the page. The era-5
  substrate it must preserve **is** present: "Yahoo Finance" (provenance badge context) and
  `structure-load-button` (the fetch control's `data-testid`) both found in the raw HTML.
- `apps/frontend/app/structure/page.tsx` is a single 1,372-line file, `grep`-confirmed to contain no
  `tradability`/`band`/`case stud`/`edge.report`/`structure_tape_map` reference — unchanged from era
  5.
- This is the dev-level code/API/SSR inspection leg only; the full click-through browser check (locate
  the default map view vs. the raw-levels toggle, confirm the fetch control + provenance badge still
  render) is the browser-qa-agent's step per the spec's TESTING REQUIREMENTS.

### J-06 — Cockpit confluence (expected FAIL) + BLOCKED (credentialed replay portion)

- `apps/frontend/components/PriceChart.tsx` (373 lines) `grep`-confirmed to contain no
  `band`/`confluence`/`chip`/`tradability` reference — the overlay and chip do not exist yet.
- The credentialed AAPL 2026-06-22 replay-and-observe half of this journey is **`blocked`** for the
  same reason as J-03: no Alpaca credentials in this environment (verified above, presence-only
  check, no value read or logged).
- This is the dev-level code inspection leg only; the browser-qa-agent's step per TESTING
  REQUIREMENTS covers the SIM-ticker honest-empty-state check and (once credentials exist) the live
  replay watch.

### J-07 — The foundation is unchanged (regression sentinel) — CONFIRMED INTACT

- Full suite green (1201/1207 above, byte-identical to the era-5 closing count); equivalence suites
  green (22/22 above); `config_fingerprint` confirmed **live-computed** as `4d665603569b9dbf`,
  matching the pinned value.
- Champion pointer confirmed untouched: live probe `GET /research/profiles` →
  `"champion":{"strategy_id":"v1","profile":"default"}`, `profiles` list unchanged (`default` frozen,
  `candidate-faster-warmup` non-default).
- `GET /meta/ui-routes` → exactly the same **6** entries as the blueprint's frozen nav (Cockpit `/`,
  Journal `/journal`, Journal detail `/journal/[id]` non-nav, Studies `/studies`, Performance
  `/performance`, Structure `/structure`) — unchanged, no new entry.
- `GET /research/strategies` → both `v1` and `structure_tape` registered with full, unchanged config
  (era-4, confirmed intact above under J-04).
- `apps/backend/tests/test_no_execution_path.py` (the anti-goal #1 tier-1 guard) confirmed present,
  unmodified (9,116 bytes, last touched 2026-07-06 — predates this session).
- Live backend (`scripts/dev.sh`, scratch ports 8301/3301): `GET /health` → `{"status":"ok"}`. Live
  frontend (`next dev`, port 3301): `GET /` → 200, `GET /journal` → 200, `GET /studies` → 200, `GET
  /performance` → 200, `GET /structure` → 200.
- `git diff --stat -- apps/` confirmed **empty** — not merely "additive" — this iteration makes no
  backend or frontend edit at all: `config.py`, `research/levels.py`, `research/backtests.py`,
  `research/strategies.py`, the engine, `research/bars.py` (the JSON `BarStore`), the Alpaca adapter,
  and `app/meta.py` are all untouched.
- **Not verified by me this iteration** (browser-qa-agent's step per TESTING REQUIREMENTS, not a
  dev-level code/API check): the sim cockpit click-through (`SIM-BUYER` settles `buyer_control`,
  `SIM-SELLER` settles `seller_control`) requires an active WebSocket-driven watch session, which is
  a browser interaction, not a GET probe — recorded as deferred, not as pass or fail.

## Files Changed

- (none — verify-only baseline; zero source modifications under `apps/`)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **1201 passed, 6 skipped** (1207 collected), 2 warnings, 366.28s, exit 0

Equivalence tests (extracted from the same run, no separate invocation): `test_observer_equivalence.py`
7/7 passed, `test_profile_equivalence.py` 15/15 passed — **22/22 total**.

Command: `cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"`
Result: `4d665603569b9dbf` — matches the pinned fingerprint exactly.

## Service startup verification

- `bash scripts/dev.sh` (deterministic scratch ports `8301`/`3301` from the script's own
  project-path hash offset) started both services clean: backend `/health` → 200 within 4s, frontend
  root → 200. No `error`/`address already in use`/`EADDRINUSE` in either log.
- Stopped both (port-based kill matching `dev.sh`'s own cleanup logic — `lsof -ti :$PORT` + `fuser -k
  -9 $PORT/tcp`), confirmed both ports fully released, then **started `dev.sh` again on the same
  ports** — backend `/health` → 200, frontend root → 200 within 4s, no port-conflict errors in the
  restart log. Stopped again; final check confirms ports `8301`/`3301` are both free and no
  tapeology `uvicorn`/`next dev` process remains bound to them.

## No side effects (baseline hygiene)

- Every live probe this iteration was a **read-only GET** (`/health`, `/research/tradability`,
  `/research/setups*`, `/research/edge-report`, `/research/bars*`, `/research/levels`,
  `/research/strategies`, `/research/profiles`, `/research/datasets`, `/tape/SIM-BUYER/history`,
  `/meta/ui-routes`, plus frontend page GETs) — no `POST`/`PUT`/`DELETE` call was made, so no
  journal/dataset/bar-series record was created or mutated.
- No Alpaca network call was made or attempted — credentials are absent (confirmed presence-only,
  values never read/logged) and this baseline needs none.
- No live Yahoo Finance network call was made — all bar reads were against the already-stored era-5
  AAPL series; correctly out of scope for a verify-only iteration.
- The frontend/backend smoke test used the real dev databases rather than a scratch path; safe given
  the read-only-GET constraint above, consistent with prior baseline practice
  (`docs/handoffs/goal-yahoo_fetch-iter-0-dev.md`).

## Known Issues

- **Environment drift (carried over from every prior era baseline):** the backend venv runs Python
  **3.14.4**; `.claude/project-template.md`'s placeholder text says 3.12. The full suite is green on
  3.14.4 — a documentation/environment drift observation, not a failure. No action taken (out of
  scope for a verify-only iteration).
- **`.claude/project-template.md` is still the generic unfilled vendored template** (confirmed again
  this iteration — same finding as every prior baseline). This developer used goal.md's Constraints
  section, prior dev handoffs (especially `docs/handoffs/goal-yahoo_fetch-iter-0-dev.md` and
  `-iter-8-dev.md`), and direct codebase inspection (`pyproject.toml`, `apps/backend/tests/`,
  `scripts/dev.sh`) as the real stack-configuration source of truth. Not this iteration's scope to
  fix.
- **J-03 and J-06 are `blocked` on operator-supplied Alpaca credentials**, exactly as the spec
  anticipates — not a code gap, not simulated. Re-run once `ALPACA_API_KEY`/`ALPACA_API_SECRET` are
  exported in the operator's environment.
- Full click-through browser verification of J-05, J-06 (SIM-ticker honest-empty-state), and J-07's
  sim-cockpit spot-checks (`SIM-BUYER`→`buyer_control`, `SIM-SELLER`→`seller_control`,
  `/journal`/`/studies`/`/performance` content, era-5 `/structure` fetch control + provenance badge
  in the browser) is the browser-qa-agent's step per the spec's TESTING REQUIREMENTS; the evidence
  above is the dev-level code/API/SSR inspection leg only.
- J-02's future builder should independently confirm 5m/1h/1d bar coverage across the full 12-symbol
  panel (`AAPL MSFT NVDA TSLA AMZN GOOGL META AMD NFLX SPY QQQ JPM`) as its own Step 1 — this baseline
  only re-confirmed AAPL's existing era-5 series.

## Suggested Next Phase

Per the spec's NOTES and goal.md's dependency order (J-01 → J-02 → J-03 → J-04, then J-05/J-06
surface them, J-07 guarding continuously): iteration 1 should build **J-01 alone** — the tradable
level map (`apps/backend/app/research/tradability.py` consuming `compute_levels` output verbatim,
config-owned band clustering/scoring/cap, morning-markup as-of discipline) + `GET
/research/tradability?symbol=&as_of=` + the read-only MCP proxy. It is the natural unblocker: J-02's
scanner walks its bands, J-04 arms `structure_tape_map` on them, and J-05/J-06 render them. The AAPL
2026-06-22 pinned case is ready to test against today — real bars and the real 1,800-level/212-zone
raw output are already in the store (confirmed above), so J-01's acceptance criteria (≤10 bands, the
300.48–302.07 resistance band ranking top-2) can be exercised immediately without any new data
fetch.
