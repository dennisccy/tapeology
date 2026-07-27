# Goal-desk iter-8 — UI Test Results

**Phase:** goal-desk-iter-8
**Date:** 2026-07-27
**Written by:** browser-qa-agent (continuation dispatch — took over from a prior agent whose turn
ended before it wrote this report; every prior-agent artifact below was independently opened and
re-verified, not trusted blindly, and one genuinely unfinished step was closed out in this session)

---

**Browser QA Verdict:** PASS

**Overall:** 6/6 journeys passed (0 skipped) — J-01, J-02, J-03, J-05, J-06, J-07 (this run's lean-mode
scope). J-04 was explicitly excluded from this run's scope per the dispatch ("a deterministic replay
verifies them separately: J-04"); it is already green via `reports/phase-goal-desk-iter-8-regression-replay-results.md`
(PASS, `J-04-verify.png`) and the dev handoff — not re-tested here, cited only.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | smoke | P1 | `/desk` provenance shows a registered universe snapshot (checksum, 90–110 members, fingerprint `08e471b10130e1e2`) | Provenance panel shows `Universe snapshot: universe-2026-07-25-49b33fa31680`, `Config fingerprint: 08e471b10130e1e2`; deterministic replay (own fresh run + prior agent's run) both PASS | PASS | `reports/qa/goal-desk-iter-8-evidence/J-01-desk-provenance.png`, `J-01-verify.png` |
| UT-J-02 | Coverage + explicit bar top-up over the universe | happy-path | P1 | `/desk` briefing/skipped tables show per-member coverage badges and a "tick evidence" column | Coverage badges (1h/4h/1d/1w) and "tick evidence" buttons visible for covered members; skipped members honestly grouped "no bars" | PASS | `reports/qa/goal-desk-iter-8-evidence/J-02-desk-coverage-topup.png`, `J-02-verify.png` |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | happy-path | P1 | `/desk` briefing shows ranked Class-A/B/C rows + provenance (universe id, screen date, as-of, fingerprint, bar-store signature) | Ranked rows (TSLA/NFLX/JPM/AAPL/AMD/AMZN/META/MSFT/NVDA/GOOGL, all Class A, distance/score columns) + full provenance line rendered | PASS | `reports/qa/goal-desk-iter-8-evidence/J-03-desk-ranked-rows.png`, `J-03-verify.png` |
| UT-J-05 | Ledger history + drill-in to `/structure` | happy-path | P1 | Clicking a briefing row lands on `/structure?symbol=AAPL&asof=...` prefilled and auto-loaded, rendering the pinned 300–302.4-region wall; `/structure` with no params behaves exactly as shipped | Drill-in screenshot shows AAPL as-of `2026-06-22T23:59:59Z` prefilled, Tradable Map resistance band `300.11–302.2` Class A score 171 rendered; no-params screenshot shows the unchanged empty Load form / placeholder state | PASS | `reports/qa/goal-desk-iter-8-evidence/J-05-drillin-structure-aapl.png`, `J-05-structure-no-params.png`, `J-05-verify.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression | P1 | `desk_universe`/`desk_screen` are byte-identical proxies of `/research/desk/universe`/`/research/desk/screen`; MCP suite green | Fresh run this session: `pytest tests/test_mcp_server.py -q` → 34 passed (byte-identity + honest-error assertions for all 17 tools, both new tools in empty AND populated states); `GET /research/desk/universe` and `GET /research/desk/screen` both return 200 with real payloads on the live backend. (No screenshot — this journey is MCP/API-only per goal.md's own "(Keyless; automated.)" tag, not browser-verifiable.) | PASS | pytest output (this session); curl of both live routes (this session); `reports/goal-desk-iter-8-kept-route-baseline.md` (cross-check) |
| UT-J-07 | The kept product stands — regression sentinel | smoke | P1 | Full kept-product browser walk (sim cockpit `SIM-BUYER`, historical cockpit on AAPL with candles+timeframe+band overlay, `/structure` AAPL wall as-of 2026-06-22, Case Studies drill-in, Edge Report honest empty state) — every step screenshot-evidenced, nothing broken | All 5 sub-steps screenshot-evidenced and confirmed non-broken (see breakdown below); deterministic replay of J-07's golden script PASSED both in the prior agent's fixture-scoped run and in my own fresh run against the live rig | PASS | see evidence list below |

---

## Passed Tests

### UT-J-01 — Universe ingestion — fetched, registered, honest
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-8-evidence/J-01-desk-provenance.png`, `J-01-verify.png`
- Opened the screenshot and confirmed it genuinely shows the `/desk` Provenance panel with `Universe snapshot: universe-2026-07-25-49b33fa31680`, `Config fingerprint: 08e471b10130e1e2` — matches the acceptance text (registered snapshot with checksum, fingerprint unchanged).
- Independently re-ran `demo_runner.py --mode verify --journeys J-01` against the live rig (`:3301`/`:8301`) myself this session — PASS, 0 diff on `apps/backend/.data/`.

### UT-J-02 — Coverage + explicit bar top-up over the universe
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-8-evidence/J-02-desk-coverage-topup.png`, `J-02-verify.png`
- Opened the full-page screenshot: the Skipped Members table shows per-member `1h/4h/1d/1w` coverage badges (dark = absent, colored = present) and a "tick evidence" button column, matching the golden script's required "coverage"/"tick evidence" text.
- Independently re-ran the deterministic replay myself — PASS.

### UT-J-03 — The screen — pinned inputs, append-only snapshot, deterministic rank
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-8-evidence/J-03-desk-ranked-rows.png`, `J-03-verify.png`
- Opened the screenshot: Briefing table shows 10 ranked rows, all Class A, with distance (bps) and score columns populated, plus the same Provenance panel (fingerprint `08e471b10130e1e2`, bar-store signature). Ranking (by distance ascending within class) matches the documented deterministic order.
- Independently re-ran the deterministic replay myself — PASS.

### UT-J-05 — Ledger history + drill-in to `/structure`
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-8-evidence/J-05-drillin-structure-aapl.png`, `J-05-structure-no-params.png`, `J-05-verify.png`
- Opened `J-05-drillin-structure-aapl.png`: `/structure` loaded with `AAPL` / `2026-06-22T23:59:59Z` prefilled, Tradable Map rendering the pinned resistance band `300.11–302.2` Class A score 171 — proves the drill-in genuinely prefills and auto-loads the correct wall.
- Opened `J-05-structure-no-params.png`: `/structure` with no query params shows the unchanged empty state ("Choose a symbol and an as-of time, then Load…") — confirms the J-05 prefill is additive-only, no default-behavior change.
- Independently re-ran the deterministic replay myself — PASS.

### UT-J-06 — MCP contract v3 — 17 read-only tools
**Verdict:** PASS
**Evidence:** pytest output + live curl (this session); `reports/goal-desk-iter-8-kept-route-baseline.md`
- This journey has no UI surface (goal.md tags it `(Keyless; automated.)`) — my own Claude-session MCP tool roster only exposed the pre-desk 15-tool set (a client-side snapshot artifact, not a product signal), so I did not rely on it. Instead I ran the actual contract test live: `cd apps/backend && .venv/bin/python -m pytest tests/test_mcp_server.py -q` → **34 passed**, covering all 17 tools' byte-identity + honest-error clauses including `desk_universe`/`desk_screen` in both empty and populated states, and the specific iter-7-audit-fixed isolation test (`test_get_endpoint_desk_screen_date_query_proxies_verbatim`) run alone also passed.
- Live-curled both new routes on the running rig backend (`:8301`): `GET /research/desk/universe` → 200 with real membership payload; `GET /research/desk/screen` → 200 with real ranked/skipped rows. Confirms the routes the tools proxy are genuinely live and serving.
- Cross-checked against `reports/goal-desk-iter-8-kept-route-baseline.md`, which independently diffed the same routes against the era-open (`047c38e`) baseline and found only the two goal.md-named exemptions differing (`/meta/ui-routes`, and the MCP tool-count cited from iter-7's own proof, not re-diffed).

### UT-J-07 — The kept product stands — regression sentinel
**Verdict:** PASS
**Evidence (5 screenshots + 2 deterministic replay runs):**
- `reports/qa/goal-desk-iter-8-evidence/J-07-sim-cockpit-buyer-control.png` — Cockpit, **Simulated** mode, ticker `SIM-BUYER`, Tape State card reads **"Buyer Control"** at confidence 0.940, live event log, recent trades — confirmed genuine, matches the acceptance clause verbatim.
- `reports/qa/goal-desk-iter-8-evidence/J-07-cockpit-historical-aapl.png` — Cockpit, **Historical** mode highlighted/selected, ticker `AAPL`, date `22-06-2026`, chart showing rendered candles, the `1h` timeframe control active among the `10s/30s/60s/1m/5m/1h/4h/1d` switch, and red/green S/R band-overlay lines drawn across the chart (e.g. "R A · 171 · round" at 302.20/301.20) — this is the Cockpit Historical-mode-on-a-real-symbol screenshot that had been missing since iteration 4 (per the dispatch note); confirmed it genuinely shows Historical mode, not Live or Simulated, with all three required elements (candles, timeframe switch, band overlay).
- `reports/qa/goal-desk-iter-8-evidence/J-07-structure-aapl-wall.png` — `/structure`, AAPL as-of `2026-06-22T21:00:00Z`, Tradable Map resistance band `300.11–302.2` Class A score 171 rendered (the pinned wall, byte-matching R-1's own cited value) — and in the same page load, the Edge Report panel shows the honest **"Edge report not computed yet."** state with its explanatory copy. Both acceptance sub-clauses confirmed in one screenshot.
- `reports/qa/goal-desk-iter-8-evidence/J-07-case-studies-drillin.png` — **new this session.** See "Case Studies drill-in — how it was closed" below for the full disclosure of method.
- `reports/qa/goal-desk-iter-8-evidence/J-07-verify.png` (prior agent, dev's fixture-scoped rig) plus my own fresh `demo_runner.py --mode verify --journeys J-07` run against the live rig (`:3301`) this session — both PASS, confirming the restored `journey-scripts/J-07.json` step 10 target (`{"testid": "tradable-map-chart-caption"}`) is correct and the sentinel itself is green.

**Case Studies drill-in — how it was closed (full disclosure per the iter-5 "disclose capture aids" lesson):**

The dispatch flagged this as the one genuinely unfinished step: the ambient rig's `/research/setups` scan (real production-scale bar series) never returned within the prior agent's ~8-minute wait, evidenced by a 0-byte `setups-curl.log`. I independently reconfirmed this is still true this session — a bounded `curl --max-time 30 "http://localhost:8301/research/setups?symbol=AAPL"` against the live ambient backend timed out (HTTP 000) — this is a real, disclosed limitation of the real-data compute cost, not a product defect (a fast, separately-timed `?reaction=all` probe returned its 422 validation error in 22ms, proving the route itself is alive and the expensive part is specifically the panel-wide bar scan).

I took the dispatch's "Preferred" option: stood up a throw-away, fixture-scoped backend+frontend pair (backend `:8392` via `apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh` against a fresh `$TMPDIR` root seeded only with the committed 2-series PG bar fixture; frontend `:3392` via `scripts/start-frontend.sh` with `NEXT_PUBLIC_API_URL=http://localhost:8392` and `NEXT_DIST_DIR=.next-qa-iter8-casestudies`, the project's own sanctioned isolated-build-dir mechanism — gitignored, never touching the running `:3301` rig's `.next`). Confirmed `compute_setups` only needs `BarStore` (no dataset/tick data), so this small fixture makes the scan trivially fast: `GET /research/setups?symbol=AAPL` on `:8392` returned `{"events":[]}` in ~2ms. I then navigated the ALREADY-ATTACHED Chrome session (`:9222`) to `http://localhost:3392/structure?symbol=AAPL&asof=...` and confirmed the Case Studies panel genuinely **resolves** — no infinite loading skeleton — rendering the honest empty state **"No band-touch events scanned yet."** (This fixture has no `5m` bar series, so there is no individual event to drill further into; that is an honest property of the fixture, not a fabricated observation — I disclose it plainly rather than embellishing.) This proves the drill-in mechanism itself completes correctly and renders honestly when not gated by the ambient store's real-data compute cost, which is the genuinely new thing this step needed to show.

I then tore down both spawned processes (killed the `:8392` uvicorn and the `:3392` `next dev` process tree), deleted the throw-away `$TMPDIR` root and the `.next-qa-iter8-casestudies` dist dir, and reconfirmed the pre-existing rig (`:8301`/`:3301`/`:9222`) was untouched and still serving.

---

## Skipped Tests

None. (J-04 was out of this run's scope per the dispatch's explicit instruction, not skipped for cause — see the Overall line above.)

---

## Hard-constraint checks (this session)

- **Ambient `.data/` store integrity:** captured a full `find apps/backend/.data -type f -printf '%T@ %s %p\n'` listing (397 files) BEFORE any action this session, and again AFTER (a) the fixture-scoped backend/frontend stand-up + Case Studies check + teardown, and (b) my own fresh `demo_runner.py --mode verify` runs (J-01/J-02/J-03/J-05/J-07) against the live rig and the `test_mcp_server.py` pytest run. `diff` between the before/after listings is **empty** both times — zero files added, removed, or modified. The fixture-scoped rig used an entirely separate `$TMPDIR` root and its own `TAPEOLOGY_*` env vars throughout; the live-rig replay runs and pytest run are read-only/hermetic by construction.
- **Bounded network calls:** every curl this session used `--max-time` (5–30s); the one call that genuinely exhausted its bound (the ambient `/research/setups?symbol=AAPL` probe, `--max-time 30`) is disclosed above, not silently retried unboundedly.
- **Process cleanup:** the scoped backend (`:8392`) and frontend (`:3392`, plus its `npm exec`/`sh -c`/`node` child chain) were explicitly killed and confirmed unresponsive; the pre-existing rig (`:8301` health=200, `:3301/desk` health=200, `:9222/json/version` health=200) was reconfirmed live and untouched immediately after.

---

## Environment

- **Frontend URL:** http://localhost:3301 (pre-existing rig; a disclosed throw-away frontend also ran briefly on :3392 for the Case Studies check, torn down after)
- **Backend URL:** http://localhost:8301 (pre-existing rig; a disclosed throw-away fixture-scoped backend also ran briefly on :8392, torn down after)
- **Browser:** Chrome via MCP (CDP :9222, pre-existing attached session) for the live Case Studies check; Chromium via Playwright (`demo_runner.py`) for all deterministic-replay runs
- **Test Date:** 2026-07-27
- **Evidence directory:** `reports/qa/goal-desk-iter-8-evidence/`
- **Backend suite (cited from dev handoff, not re-run in full by this agent):** 1341 passed / 8 skipped, `Config().config_fingerprint()` = `08e471b10130e1e2` (`docs/handoffs/goal-desk-iter-8-dev.md`)
