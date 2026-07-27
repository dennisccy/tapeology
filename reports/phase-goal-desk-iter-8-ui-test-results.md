# UI Test Results (merged)

**Date:** 2026-07-27
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-8-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to `/structure` | happy-path | P1 | Clicking a briefing row lands on `/structure?symbol=AAPL&asof=...` prefilled and auto-loaded, rendering the pinned 300–302.4-region wall; `/structure` with no params behaves exactly as shipped | Drill-in screenshot shows AAPL as-of `2026-06-22T23:59:59Z` prefilled, Tradable Map resistance band `300.11–302.2` Class A score 171 rendered; no-params screenshot shows the unchanged empty Load form / placeholder state | PASS | `reports/qa/goal-desk-iter-8-evidence/J-05-drillin-structure-aapl.png`, `J-05-structure-no-params.png`, `J-05-verify.png` |
| UT-J-01 | Universe ingestion — fetched, registered, honest | smoke | P1 | `/desk` provenance shows a registered universe snapshot (checksum, 90–110 members, fingerprint `08e471b10130e1e2`) | Provenance panel shows `Universe snapshot: universe-2026-07-25-49b33fa31680`, `Config fingerprint: 08e471b10130e1e2`; deterministic replay (own fresh run + prior agent's run) both PASS | PASS | `reports/qa/goal-desk-iter-8-evidence/J-01-desk-provenance.png`, `J-01-verify.png` |
| UT-J-02 | Coverage + explicit bar top-up over the universe | happy-path | P1 | `/desk` briefing/skipped tables show per-member coverage badges and a "tick evidence" column | Coverage badges (1h/4h/1d/1w) and "tick evidence" buttons visible for covered members; skipped members honestly grouped "no bars" | PASS | `reports/qa/goal-desk-iter-8-evidence/J-02-desk-coverage-topup.png`, `J-02-verify.png` |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | happy-path | P1 | `/desk` briefing shows ranked Class-A/B/C rows + provenance (universe id, screen date, as-of, fingerprint, bar-store signature) | Ranked rows (TSLA/NFLX/JPM/AAPL/AMD/AMZN/META/MSFT/NVDA/GOOGL, all Class A, distance/score columns) + full provenance line rendered | PASS | `reports/qa/goal-desk-iter-8-evidence/J-03-desk-ranked-rows.png`, `J-03-verify.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression | P1 | `desk_universe`/`desk_screen` are byte-identical proxies of `/research/desk/universe`/`/research/desk/screen`; MCP suite green | Fresh run this session: `pytest tests/test_mcp_server.py -q` → 34 passed (byte-identity + honest-error assertions for all 17 tools, both new tools in empty AND populated states); `GET /research/desk/universe` and `GET /research/desk/screen` both return 200 with real payloads on the live backend. (No screenshot — this journey is MCP/API-only per goal.md's own "(Keyless; automated.)" tag, not browser-verifiable.) | PASS | pytest output (this session); curl of both live routes (this session); `reports/goal-desk-iter-8-kept-route-baseline.md` (cross-check) |
| UT-J-07 | The kept product stands — regression sentinel | smoke | P1 | Full kept-product browser walk (sim cockpit `SIM-BUYER`, historical cockpit on AAPL with candles+timeframe+band overlay, `/structure` AAPL wall as-of 2026-06-22, Case Studies drill-in, Edge Report honest empty state) — every step screenshot-evidenced, nothing broken | All 5 sub-steps screenshot-evidenced and confirmed non-broken (see breakdown below); deterministic replay of J-07's golden script PASSED both in the prior agent's fixture-scoped run and in my own fresh run against the live rig | PASS | see evidence list below |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-27

