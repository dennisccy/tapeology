# Goal Iteration goal-desk-iter-0 — UI Test Results

**Phase:** goal-desk-iter-0
**Date:** 2026-07-25
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- This is a BASELINE assessment iteration (Mode: baseline, iter-0 of session `desk`, Era B
     "The Desk"). Per docs/phases/goal-desk-iter-0.md, J-01 through J-06 are EXPECTED to FAIL
     (none of the desk era's capabilities have been built yet — zero code changes this
     iteration, confirmed via `git diff --stat 047c38e -- apps/` = empty) and J-07 (the
     kept-product regression sentinel) is EXPECTED to PASS on its KEPT-behavior evidence. The
     verdict above tracks J-07 — the one journey that gates "does the already-shipped product
     still work" — which passed with strong, fully-browser-verified evidence, including sections
     (Case Study drill-in, Edge Report honest state) that a prior era's baseline iteration
     (`fast_wall`) had to skip for operational-safety reasons. J-01-J-06 FAILing is the correct,
     desired baseline recording, not a QA or pipeline malfunction. J-01–J-06 are scored P2
     (baseline-probe; a not-yet-built future capability cannot fail the "kept product" gate);
     J-07 is P1 (the actual regression risk this iteration could have exposed). See "Baseline
     Context" below. -->

**Overall:** 1/7 journeys PASS (J-07, kept-behavior evidence — full era acceptance for J-07
itself, e.g. 3-route nav / 17-tool MCP, is not yet satisfiable and is explicitly not scored as a
failure per the iteration spec), 6/7 journeys FAIL as expected for a pre-build baseline
(J-01–J-06), 0 SKIPPED — every journey received a fully evidenced verdict.

---

## Baseline Context

This is iteration 0 (`Mode: baseline`) of the brand-new `desk` goal-mode session (Era B "The
Desk") — a verify-only iteration with **zero source changes** (`git diff --stat 047c38e --
apps/` returned empty throughout this QA pass; `git status --short` shows only new
report/doc/runs artifacts, no `apps/` edits). Its purpose is to record which of J-01–J-07 already
pass/fail against the current (post-`clean_slate`, pre-desk) codebase. Per the iteration spec:
*"J-01 through J-06 are expected to be recorded FAILING this iteration — this is the honest,
expected baseline for a not-yet-started era, not a defect."* All 7 results below match that
prediction exactly, and every backend-absence claim below is backed by a live grep/curl run this
session (not copied from the decomposer's decompose-time notes), including a conclusive
whole-tree check: `grep -rn "desk" apps/backend/app/research/routes.py apps/backend/app/main.py`
and `grep -rn "research/desk\|desk_universe\|desk_screen" apps/backend/app/` both returned **zero
matches** — no desk route exists under any name, anywhere in the backend.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | baseline-probe | P2 | `GET /research/desk/universe` serves honest empty/registered payload; universe store, parser, fixture, and Path-A Config fields exist | `GET /research/desk/universe` → HTTP 404; `POST /research/desk/universe/fetch` → HTTP 404; zero matches for `desk` anywhere under `apps/backend/app/research/` or `apps/backend/tests/fixtures/`; zero matches for `desk_universe_source_url`/`desk_universe_min_members`/`desk_universe_max_members` in `config.py`; no `.data/universe/` directory — feature not yet built | FAIL (expected at baseline) | none (non-browser backend/grep check; see Failed Tests below) |
| UT-J-02 | Coverage + explicit bar top-up over the universe | baseline-probe | P2 | `GET /research/desk/coverage` serves per-member bar coverage from `bar_index`; an operator-run top-up (POST + CLI, compute-manager pattern) exists | `GET /research/desk/coverage` → HTTP 404; `POST /research/desk/universe/top-up` and `POST /research/desk/coverage/top-up` → HTTP 404 (both plausible sub-paths absent; the whole-tree grep above confirms no `/research/desk/*` route of any name is registered) — feature not yet built | FAIL (expected at baseline) | none |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | baseline-probe | P2 | `GET /research/desk/screen` serves the honest "Desk screen not computed yet." payload or ranked rows; screen compute (POST + CLI) exists | `GET /research/desk/screen` → HTTP 404; `POST /research/desk/screen/compute` → HTTP 404; no `desk_screen.py` under `apps/backend/app/research/` — feature not yet built | FAIL (expected at baseline) | none |
| UT-J-04 | The `/desk` briefing page | smoke | P2 | Nav shows Cockpit · Structure · Desk; `/desk` renders the latest-screen briefing or the honest "Desk screen not computed yet." empty state | Navigated to `http://localhost:3301/desk` — Next.js rendered its honest built-in 404 ("This page could not be found."); nav shows exactly 2 entries (Cockpit, Structure), no Desk entry; `GET /meta/ui-routes` confirms exactly 2 route objects (`/`, `/structure`) — `/desk` not yet built | FAIL (expected at baseline) | `reports/qa/goal-desk-iter-0-evidence/J-04-desk-404.png` |
| UT-J-05 | Ledger history + drill-in to `/structure` | smoke | P2 | `/structure?symbol=AAPL&asof=2026-06-22` prefills the Load form's Symbol/As-of inputs and auto-Loads | Navigated to `http://localhost:3301/structure?symbol=AAPL&asof=2026-06-22` — Symbol input `value=""` and As-of input `value=""` (both confirmed empty via rendered DOM), Load button stayed `disabled`; Tradable Map showed "∅ Choose a symbol and an as-of time, then Load..." — no auto-Load fired; `grep -n "useSearchParams\|searchParams" apps/frontend/app/structure/page.tsx` → zero matches — prefill not yet built | FAIL (expected at baseline) | `reports/qa/goal-desk-iter-0-evidence/J-05-structure-no-prefill.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools | baseline-probe | P2 | MCP server advertises exactly 17 tools including `desk_universe`/`desk_screen` | `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` tuple inspected live — exactly 15 entries (`tape_state` … `get_endpoint`), no `desk_universe`/`desk_screen` present — still the pre-desk 15-tool contract | FAIL (expected at baseline) | none |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | Full backend suite green; `config_fingerprint` = `08e471b10130e1e2`; Cockpit `SIM-BUYER` settles `buyer_control` with chart candles + timeframe switch + S/R band overlay + live tape bar; `/structure` Load for pinned AAPL `2026-06-22` renders the 300–302.4 wall band; a Case Study drill-in opens; Edge Report shows warm cells or the honest "not computed yet" panel. (J-07's own literal acceptance also names a 3-route nav / 17-tool MCP — not yet satisfiable until J-04/J-06 ship; scored as pending per the iteration spec, not as a KEPT-product failure.) | Suite: **1169 passed, 7 skipped, 0 failed** (128.85s, exit 0) — matches `docs/goal.md`'s cited era-open baseline exactly. `Config().config_fingerprint()` = `08e471b10130e1e2`, confirmed live. Cockpit: `SIM-BUYER` settled **Buyer Control** (confidence 0.82–0.95 across two runs); live 10s logical tape bars rendered and moved; the chart's own `Tape` 10s→30s timeframe toggle switched (`aria-pressed` confirmed); switched Cockpit to `Historical` mode with real AAPL data (22-06-2026, Full RTH) — real SIP-fed candles rendered with a full S/R band overlay (resistance `300.10–302.20` Class A round-number band) across the `History` 1m/5m/1h/4h/1d timeframe buttons — the same `StructureChart` canvas component confirmed by DOM (`data-testid="structure-chart-canvas"` reused for both Cockpit and Structure). `/structure`: loaded AAPL as-of `2026-06-22T21:00:00Z` — resistance band `300.11–302.2 Class A` rendered on the Tradable Map / `StructureChart` (the cited "300–302" wall, cross-consistent with the Cockpit reading above); Case Studies list populated (819 AAPL rows once the backend's setups-scan cache warmed — see Supporting probe evidence below); clicked a row — the drill-in panel opened showing `symbol/session: AAPL · 2025-01-02`, band, `reaction: rejected`, forward returns, and the honest `"No recorded tape for this event."` state; Edge Report section showed the honest **"Edge report not computed yet."** panel with an enabled Compute button. Nav-route-count (2, not 3) and MCP tool-count (15, not 17) — the two desk-completion clauses of J-07's literal acceptance — are correctly NOT YET satisfiable this iteration (they depend on J-04/J-06) and are scored as pending, not as a regression, per the iteration spec's explicit framing. | **PASS** (kept-behavior evidence; full-era acceptance clauses pending J-04/J-06) | `reports/qa/goal-desk-iter-0-evidence/J-07-cockpit-sim-buyer-control.png`, `J-07-cockpit-tape-30s-switch.png`, `J-07-cockpit-historical-1d-band-overlay.png`, `J-07-structure-aapl-wall.png`, `J-07-structure-case-study-drillin.png` (+3 more, see Evidence dir) |

---

## Passed Tests

### UT-J-07 — The kept product stands — regression sentinel
**Verdict:** PASS (kept-behavior evidence; the 3-route-nav / 17-tool-MCP clauses of J-07's full
acceptance are correctly pending J-04/J-06, per the iteration spec — not scored as a failure)

**Evidence:**
- `reports/qa/goal-desk-iter-0-evidence/J-07-cockpit-sim-buyer-control.png`
- `reports/qa/goal-desk-iter-0-evidence/J-07-cockpit-tape-30s-switch.png`
- `reports/qa/goal-desk-iter-0-evidence/J-07-cockpit-tape-60s.png` (Features-panel timeframe, supplementary)
- `reports/qa/goal-desk-iter-0-evidence/J-07-cockpit-historical-aapl-band.png` (connecting state)
- `reports/qa/goal-desk-iter-0-evidence/J-07-cockpit-historical-1d-band-overlay.png`
- `reports/qa/goal-desk-iter-0-evidence/J-07-structure-aapl-wall.png`
- `reports/qa/goal-desk-iter-0-evidence/J-07-structure-case-studies-list.png` (raw full-page, 819 rows)
- `reports/qa/goal-desk-iter-0-evidence/J-07-structure-case-study-drillin.png`

**Step 1 — full backend suite + fingerprint.** Ran `apps/backend/.venv/bin/python -m pytest
tests/ -v`: **"1169 passed, 7 skipped, 2 warnings"** in 128.85s, exit code 0. Matches
`docs/goal.md`'s cited era-open baseline (1169 pass / 7 skip) exactly — no drift.
`python -c "from app.config import Config; print(Config().config_fingerprint())"` (run from
`apps/backend`) printed `08e471b10130e1e2`, matching the pinned value.

**Step 2 — sim cockpit (`SIM-BUYER` → `buyer_control`, PriceChart capabilities).** Navigated to
`/`, mode was already `Simulated` (default), typed `SIM-BUYER` into the Ticker field, clicked
Watch: Tape State panel read **"Buyer Control"** (confidence 0.950 at one capture, 0.820/0.947 at
others as the sim continued), `scenario: buyer_control` badge present, event log read "Tape state
changed to buyer_control" — settlement confirmed. The `PRICE CHART` section's own `Tape` group
(`10s`/`30s`/`60s`, `aria-label="Tape bar size"`) showed live green/red bars building in real time
("Logical 10s bars built live from the tape.") with price ticking; clicking `30s` flipped
`aria-pressed` from the `10s` button to the `30s` button — the chart's timeframe switch confirmed
working. For SIM-BUYER specifically, `History` correctly showed "No recorded bars for SIM-BUYER"
and the Tradable Map correctly showed "No tradable map for SIM-BUYER" — the honest, correct
behavior for a synthetic ticker with no real market data (no fabricated band/candle data).

To directly verify the **S/R band overlay** and **recorded candles** clauses (which a synthetic
ticker legitimately cannot exercise), I additionally switched Cockpit to `Historical` mode with a
real symbol: `AAPL`, `22-06-2026`, `Full RTH 9:30–16:00 ET`, clicked Watch. This streamed real
`SIP (consolidated)` feed data (`scenario: historical AAPL 22-06-2026 14:30-22-06-2026 21:00`) —
Tape State again settled **Buyer Control**. Clicking the `History` group's `1d` button rendered
real recorded 1-day candles (Feb–Jul 2026) **with a full S/R band overlay** drawn on the same
chart: `R A · 171 · round · 302.20`, `R A · 97 · round · 300.10`, `R A · 92.7 · 312.97`, `R A ·
100.7 · 310.79`, `R A · 88.7 · 306.47`, plus five support bands — confirming candles + timeframe
switch + band overlay + live tape bar all still render as shipped. The `300.10–302.20` band here
is consistent with the `/structure` page's own read of the same wall (Step 3), confirming
single-source-of-truth across pages.

**Step 3 — `/structure` Load for pinned AAPL `2026-06-22`.** Navigated to `/structure` (no query
params — confirms the unprefilled default separately from J-05's test), typed `AAPL` into Symbol,
typed `2026-06-22T21:00:00Z` into As-of, clicked Load. The Tradable Map rendered:
`resistance 300.11–302.2 Class A score 171 members 849 [round number]` — the cited "300–302" wall
— plus four more resistance bands and five support bands, on the `StructureChart` canvas with
candles and the `as-of` marker. `CHART TIMEFRAME` selector (`1m 5m 1h 4h 1d 1w`) was present.

**Step 4 — Case Study drill-in.** The Case Studies table populated (819 rows for AAPL after the
backend's setups-scan cache warmed — see Supporting probe evidence). Clicked the first row
(`tr[data-testid="case-studies-row"]`): `aria-selected` flipped to `true` and a
`data-testid="case-drillin"` panel appeared reading `symbol/session: AAPL · 2025-01-02`,
`band: resistance · 251.67…–251.67… · Unclassified`, `reaction: rejected`, forward returns
(`78b: -0.0235 · 234b: -0.0365`), and `TAPE TIMELINE: "No recorded tape for this event."` — the
correct honest state for a touch with no dataset recorded around it. Drill-in opening + rendering
real per-touch detail confirmed.

**Step 5 — Edge Report honest state.** Both before and after the AAPL Load, the Edge Report
section showed: **"Edge report not computed yet."** — *"The 3-way strategy-comparison sweep has
not been run for the current dataset registry and configuration. It never runs automatically on a
GET — an operator must trigger the compute."* — with an enabled "Compute edge report" button. This
is one of the two honest states J-07's acceptance allows (warm cells OR this panel); the
GET-never-computes rule was not violated (the page load did not trigger a sweep).

**Step 6 — pending clauses, explicitly not scored as failures.** `GET /meta/ui-routes` lists
exactly 2 routes (not 3) and `EXPECTED_TOOLS` lists exactly 15 tools (not 17) — both are
desk-completion clauses of J-07's literal acceptance text that cannot be satisfied until J-04 and
J-06 ship, per the iteration spec's explicit carve-out ("J-07's own acceptance text ... requires
... which are desk-completion clauses that cannot be satisfied until J-04/J-06 ship"). Recorded
here as pending, not as a regression of the kept product.

Golden replay script written: `runs/goal-session-desk/journey-scripts/J-07.json` (covers the
Cockpit SIM-BUYER settling flow + the `/structure` AAPL `2026-06-22` Load flow; linted clean via
`demo_runner.py --mode lint`). The Historical-AAPL band-overlay excursion and the Case
Study/Edge-Report drill-ins are not encoded in the script (the golden-script format only supports
`goto`/`click`/`fill` with a single text assertion per step, and the case-studies fetch is
latency-variable — see below — making it a poor fit for a fast deterministic replay check); those
remain LLM-verified checks for future iterations.

---

## Failed Tests

<!-- All six of these are the EXPECTED, CORRECT baseline result for a pre-build iteration — see
     "Baseline Context" above. Each entry cites the exact route/grep evidence gathered THIS
     session. -->

### UT-J-01 — Universe ingestion — fetched, registered, honest
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** No universe subsystem exists yet.

**Evidence:**
- `curl http://localhost:8301/research/desk/universe` → `HTTP 404`
- `curl -X POST http://localhost:8301/research/desk/universe/fetch` → `HTTP 404`
- `grep -ril "desk" apps/backend/app/research/` → no matches (no `desk_universe.py`)
- `grep -ril "desk" apps/backend/tests/fixtures/` → no matches (no universe fixture)
- `grep -n "desk_universe" apps/backend/app/config.py` → no matches (no Path-A Config fields)
- `ls apps/backend/.data/` → `bar_index.db, bars, dataset_index.db, datasets,
  edge_report_backtests.db, edge_report_cache.db, scoped_browser_qa, setups_scan_cache.db,
  tradability_cache.db` — no `universe/` directory

**Expected:** With no snapshot, `GET /research/desk/universe` serves the honest empty payload;
after registering the fixture, it lists checksum + member count.
**Actual:** The route, module, fixture, and Config fields do not exist. Confirmed absent, not
partially built.

---

### UT-J-02 — Coverage + explicit bar top-up over the universe
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** No coverage read or top-up subsystem exists yet.

**Evidence:**
- `curl http://localhost:8301/research/desk/coverage` → `HTTP 404`
- `curl -X POST http://localhost:8301/research/desk/universe/top-up` → `HTTP 404`
- `curl -X POST http://localhost:8301/research/desk/coverage/top-up` → `HTTP 404`
- Whole-tree grep (`grep -rn "research/desk\|desk_universe\|desk_screen" apps/backend/app/`) →
  zero matches — confirms no route under any name in this family is registered, independent of
  which exact sub-path the eventual build chooses (per `blueprint.md`, that choice is still open)

**Expected:** Coverage for the fixture universe reports bars-present/-missing per member; a
top-up run completes with honest per-symbol outcomes.
**Actual:** No route, module, or Config field exists. Confirmed absent.

---

### UT-J-03 — The screen — pinned inputs, append-only snapshot, deterministic rank
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** No screen-compute subsystem exists yet.

**Evidence:**
- `curl http://localhost:8301/research/desk/screen` → `HTTP 404`
- `curl -X POST http://localhost:8301/research/desk/screen/compute` → `HTTP 404`
- `grep -ril "desk" apps/backend/app/research/` → no matches (no `desk_screen.py`)

**Expected:** On the fixture universe + fixture bars, a screen run produces ranked + skipped
rows; `GET /research/desk/screen` serves the honest "Desk screen not computed yet." before any
run.
**Actual:** The route and module do not exist. Confirmed absent.

---

### UT-J-04 — The `/desk` briefing page
**Verdict:** FAIL (expected at baseline)
**Failure:** `/desk` is not a registered route; nav has not grown a third entry.

**Steps taken:**
1. Navigated Chrome to `http://localhost:3301/desk`.
2. Extracted the rendered page markdown/DOM.
3. Cross-checked `GET /meta/ui-routes`.

**Expected:** Nav shows Cockpit · Structure · Desk; `/desk` renders a briefing table or the
honest "Desk screen not computed yet." empty state with an enabled Run Screen button.
**Actual:** Page rendered Next.js's built-in **"404 — This page could not be found."** The
top nav (present even on the 404 page) showed exactly two links: `Cockpit` → `/` and `Structure`
→ `/structure` — no Desk entry. `GET /meta/ui-routes` returned
`{"routes":[{"path":"/","label":"Cockpit","nav":true},{"path":"/structure","label":"Structure","nav":true}]}`
— exactly 2 route objects, confirming the UI and the backend agree: the page and its nav entry do
not exist yet.

**Evidence:** `reports/qa/goal-desk-iter-0-evidence/J-04-desk-404.png`

---

### UT-J-05 — Ledger history + drill-in to `/structure`
**Verdict:** FAIL (expected at baseline)
**Failure:** `/structure`'s Load form ignores `?symbol=&asof=` query params entirely; no prefill,
no auto-Load.

**Steps taken:**
1. `grep -n "useSearchParams\|searchParams" apps/frontend/app/structure/page.tsx` → zero matches.
2. Navigated Chrome to `http://localhost:3301/structure?symbol=AAPL&asof=2026-06-22`.
3. Inspected the rendered Symbol and As-of input elements' `value` attributes directly in the DOM.
4. Extracted page text to check whether an auto-Load fired.

**Expected:** The Symbol input reads `AAPL`, the As-of input reads a value derived from
`2026-06-22`, and the Tradable Map auto-loads and renders the pinned wall.
**Actual:** `<input aria-label="Structure symbol" ... value="">` and
`<input data-testid="structure-as-of-input" ... value="">` — both empty despite the query
params. The Load button stayed `disabled` (its `disabled` attribute requires both fields
populated). The Tradable Map section showed: *"∅ — Choose a symbol and an as-of time, then Load,
to see its tradable level map."* — no auto-Load occurred. Source grep confirms this is because no
prefill logic exists yet, not a rendering bug.

**Evidence:** `reports/qa/goal-desk-iter-0-evidence/J-05-structure-no-prefill.png`

---

### UT-J-06 — MCP contract v3 — 17 read-only tools
**Verdict:** FAIL (expected at baseline)
**Failure (= confirmed absence):** MCP surface still advertises the pre-desk 15-tool contract.

**Evidence:**
```
apps/backend/tests/test_mcp_server.py:49
EXPECTED_TOOLS = (
    "tape_state", "tape_features", "tape_history", "datasets", "bars", "levels",
    "tradability", "setups", "backtests", "strategies", "edge_report", "pnl_ledger",
    "taxonomy", "ui_route_map", "get_endpoint",
)
```
Exactly 15 entries; neither `desk_universe` nor `desk_screen` present.

**Expected:** 17 entries, including `desk_universe` and `desk_screen`.
**Actual:** 15 entries. Confirmed unchanged from the pre-desk contract.

---

## Skipped Tests

None at the journey level — every one of J-01–J-07 received a fully evidenced PASS/FAIL verdict.
No Chrome MCP or frontend/backend availability issue occurred this run (frontend `:3301` and
backend `:8301` were both up throughout; Chrome attached cleanly to the pre-launched isolated
instance on `127.0.0.1:9222`).

---

## Supporting probe evidence

### `GET /research/setups?symbol=AAPL` latency (J-07 Step 4 support)

The Case Studies section on `/structure` appeared to hang in a loading skeleton state for an
extended period during the first AAPL load. Direct measurement:

```
First call (cold, this backend instance's first setups scan since it started at 02:33):
  did not return within 120s per-command timeout; completed at ~9-11 min elapsed
  (backend process pinned near 96% CPU for the duration — genuinely computing, not hung)
Second call (warm, same query, immediately after):
  HTTP 200 in 0.840381s
```

This matches the documented pattern from the `fast_wall` era (durable setups-scan cache: cold
scan is slow, warm reads are near-instant) — this scoped browser-QA backend instance
(`.data/scoped_browser_qa`, started fresh at 02:33 today) simply had a cold cache for this
specific query. Not a regression: the UI's loading-skeleton state was honest and correct
throughout (no error, no stale/fabricated data shown), and the drill-in worked correctly once the
warm response arrived. Flagging this as an operational note relevant to the desk era's own J-02
requirement ("coverage GET latency is index-read fast, no store re-hash") and to future
browser-QA runs against this scoped backend instance (the first `/structure` Case Studies load of
a session may need a longer wait budget than later ones).

---

## Golden replay scripts written this iteration

- `runs/goal-session-desk/journey-scripts/J-07.json` — covers the Cockpit `SIM-BUYER` →
  `Buyer Control` settling flow and the `/structure` AAPL `2026-06-22` Load flow (asserts the
  `300.11` band text renders). Linted clean (`demo_runner.py --mode lint --scripts-dir
  runs/goal-session-desk/journey-scripts --journeys J-07` → `J-07 ok`).
- No scripts written for J-01–J-06 (all verified FAIL/absent — nothing exists yet to replay; a
  golden script is only useful for guarding an already-passing behavior).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (scoped browser-QA data dir, `.data/scoped_browser_qa`)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), attached to
  the pre-launched isolated headless instance on `127.0.0.1:9222`
- **Test Date:** 2026-07-25
- **Backend suite:** 1169 passed, 7 skipped, 0 failed (128.85s, exit 0) — matches `docs/goal.md`'s
  cited era-open baseline exactly
- **config_fingerprint:** `08e471b10130e1e2` (confirmed live, matches the frozen pin)
- **`git diff --stat 047c38e -- apps/`:** empty throughout (zero source changes this iteration)
- **Evidence directory:** `reports/qa/goal-desk-iter-0-evidence/`
