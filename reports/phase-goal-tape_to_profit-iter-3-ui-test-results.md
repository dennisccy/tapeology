# UI Test Results (merged)

**Date:** 2026-07-03
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 4/4 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-03 | Strategy grammar v1 backtests a dataset into a deterministic PnL report | functional | P1 | `GET /research/backtests` flips 404→200; a keyless POST→poll→done run yields per-trade fills, net/gross R and $, win rate, max drawdown, n, a seeded null baseline, full provenance, and the simulated register; an identical re-run reproduces a byte-identical result; unknown dataset→404, non-default profile→422, unknown strategy→422 | All confirmed via genuine in-page `fetch()` from the backend origin: 200 flip confirmed; POST+poll produced a `done` report with 5 trades, aggregates (net_r -1.239, gross_r -0.644, net_usd -123.93, gross_usd -64.40, win_rate 0.2, max_drawdown_r 1.239, n=5), null baseline (seed 1729, entry_count 100, n 100), full provenance (dataset id+checksum+window+feed echoed verbatim, strategy config echoed verbatim, profile "default", `config_fingerprint` matching top-level), register string exact match; two independent POSTs produced **byte-identical** `result` blocks (59,157 chars each) while `id`/`created_wall_ts` differed; unknown dataset→404 (`"no dataset with id 'does-not-exist-xyz'"`), non-default profile→422, unknown strategy→422 | PASS | `reports/qa/goal-tape_to_profit-iter-3-evidence/J-03-01-backtests-200-flip.png`, `J-03-02-backtest-done-detail.png`, `J-03-03-error-legs-404-422.png` |
| UT-J-02 | Historical tape datasets persist and replay byte-identically (train/hold-out registry) — regression | functional | P1 | Dataset list/detail still serve full metadata; re-tagging a registered split still returns 409; unknown id still 404; watching a live/sim ticker still writes zero dataset rows | `GET /research/datasets` 200 with the same 3 datasets from iter-2 (2 train + 1 holdout), full metadata (symbol, UTC window, feed, event counts, checksum) intact; detail route 200 (`{"dataset": {...}}`) with verbatim metadata; re-tag attempt (identical reference-window content, different split) → 409 with the exact frozen-tag message naming the existing id; unknown id → 404; full `POST /watch/SIM-BUYER` → wait → `DELETE /watch/SIM-BUYER` cycle via the canonical backend endpoint left the dataset list byte-for-byte unchanged (3 ids before and after) | PASS | `reports/qa/goal-tape_to_profit-iter-3-evidence/J-02-01-datasets-list-regression.png`, `J-02-02-cockpit-frontend-healthy.png` |
| UT-J-01 | A read-only MCP server exposes the product over the canonical API — regression (fallback, replay crashed) | functional | P1 | `GET /meta/ui-routes` lists exactly the live routes; rendered top-bar nav matches it | `GET /meta/ui-routes` → 200, 4 entries: Cockpit `/` (nav), Journal `/journal` (nav), Journal detail `/journal/[id]` (not nav), Studies `/studies` (nav) — correctly still no `/performance` entry (J-05 not shipped). Rendered nav bar on a clean page load showed exactly "Cockpit · Journal · Studies", matching the 3 nav-flagged routes. (MCP stdio byte-identity and the sync self-test are non-browser surfaces and are covered by the backend/MCP test suite, consistent with goal.md tagging most of J-01 automated, not browser-verifiable.) | PASS | `reports/qa/goal-tape_to_profit-iter-3-evidence/J-01-01-ui-routes.png`, `J-08-01-journal-page.png` (nav visible in both) |
| UT-J-08 | The existing product is unchanged (regression sentinel) — fallback, replay crashed | functional | P1 | Cockpit panels populate/classify (SIM-BUYER → buyer_control); journal and studies pages render their data | `/journal` renders correctly: heading, filters (Theses/Analytics/Hints, setup/direction/status dropdowns), "No theses journaled yet" empty state with guidance text. `/studies` renders correctly (verified via genuine page-text extraction): "Replay studies" heading, New-study form (source/setup/direction), "No studies yet" empty state. SIM-BUYER watch→state→stop cycle via the canonical backend endpoint (the same action the cockpit's Watch button triggers) settled to `tape_state: "buyer_control"`, `confidence: 0.94`, `stream_status: "live"` after 6s, then stopped cleanly (200/200). One planned artifact — a live "Buyer Control" **screenshot** of the cockpit UI itself (as opposed to the equivalent backend-verified classification) — could not be captured; see Notes | PASS | `reports/qa/goal-tape_to_profit-iter-3-evidence/J-08-01-journal-page.png`; studies page content captured as extracted text in this report (screenshot attempt failed — see Notes); SIM-BUYER classification captured as eval output (see Notes) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-03

