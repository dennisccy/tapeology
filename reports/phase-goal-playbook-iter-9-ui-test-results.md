# UI Test Results (merged)

**Date:** 2026-08-11
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-9-evidence/J-01-verify.png |
| UT-J-02 | Every signal measured — the rail's own conventions, anchored at the trigger bar | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-9-evidence/J-02-verify.png |
| UT-J-03 | The Playbook lands on /desk | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-9-evidence/J-03-verify.png |
| UT-J-04 | The continuation family — JBE, DBI, cup-and-handle | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-9-evidence/J-04-verify.png |
| UT-J-05 | The climax family — capitulation entry, euphoria marker | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-9-evidence/J-05-verify.png |
| UT-J-06 | The range family — range trades, double top/bottom | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-9-evidence/J-06-verify.png |
| UT-J-07 | The back-scan — every recorded session, resumable and append-only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-9-evidence/J-07-verify.png |
| UT-J-08 | The evidence view — distributions beside the null, min-n honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-9-evidence/J-08-verify.png |
| UT-J-09 | MCP contract v4 — 20 read-only tools | integration (keyless/automated) | P1 | Exactly 20 MCP tools incl. `desk_playbook`/`desk_playbook_evidence`, byte-identical to curl in empty AND populated fixture states, `get_endpoint` proxies `?date=` verbatim, MCP suite green | `tests/test_mcp_server.py`: 46 passed, 0 failed, exit 0 (isolated real-uvicorn instance + temp journal DB, per-module `mcp_env` fixture — touches neither the real store nor the scoped rig). `EXPECTED_TOOLS` includes `desk_playbook`/`desk_playbook_evidence`; both byte-identity tests (empty + populated state) and the `?date=` `get_endpoint` proxy test are present and pass. No browser page exists for this journey (goal.md marks it "Keyless; automated") | PASS | none (no browser surface; see note below) |
| UT-J-10 | The kept product stands — regression sentinel | browser (full kept-product walk) | P1 | Full backend suite green under pin `08e471b10130e1e2` (developer-verified: 2163 passed/8 skipped, see dev handoff); every kept browser surface (cockpit sim tape+chart, `/structure` pinned-AAPL Load, every shipped `/desk` section) screenshots unchanged; Playbook Evidence section visibly shows the built-from signature; nav = exactly 3 routes; MCP = exactly 20 tools | Cockpit: watched SIM-BUYER, live chart/tape-state/quote/features/trades/observations/event-log all populated. Structure: loaded pinned AAPL as-of 2026-06-22, tradable map shows the real 300.11–302.2 resistance band + registry (v1/structure_tape/structure_tape_map). Desk: Screen History calendar, Forward Returns, Run Screen/Top-up/Reconcile/Deep-Backfill controls, Briefing, Skipped Members, Top-up Runs, Index Reconciliation, Screen Runs, Screen Comparison, and Provenance all rendered correctly (populated via one safe `Run Screen` + `Compute Forward` click pair on the scoped fixture rig — see note below); Playbook Signals and Backscan sections render as shipped; Playbook Evidence section shows "Built from signature: `9597251432bd9e75`" above the register paragraph (the exact iter-9 addition). Nav bar shows exactly Cockpit/Structure/Desk. `Config fingerprint 08e471b10130e1e2` visible verbatim in the Provenance panel. Golden replay script recorded and verified PASS. Kept-route byte-identity / cumulative-diff-inventory checks are backend/auditor-level static diffs, outside browser-QA's testing-requirements scope for this journey (goal.md's own TESTING REQUIREMENTS lists byte-identity diffing under "Unit/integration", not "Browser") — not independently re-verified by this agent | PASS | `reports/qa/goal-playbook-iter-9-evidence/J-10-cockpit-simtape.png`, `J-10-structure-aapl.png`, `J-10-desk-top.png`, `J-10-desk-screenhistory-forward.png`, `J-10-desk-briefing-skipped-crop.png`, `J-10-desk-runs-provenance-crop.png`, `J-10-desk-playbook-signals-backscan-crop.png`, `J-10-desk-evidence-signature-crop.png`, `J-10-desk-fullpage.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-11

