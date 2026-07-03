# UI Test Results (merged)

**Date:** 2026-07-03
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | A read-only MCP server exposes the product over the canonical API | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-4-evidence/J-01-verify.png |
| UT-J-08 | The existing product is unchanged (regression sentinel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-4-evidence/J-08-verify.png |
| UT-J-02 | Historical tape datasets persist and replay byte-identically (train/hold-out registry) | regression | P1 | committed PG_SIP_REFERENCE fixture pair listed with symbol/window/feed/checksum/split; re-tagging already-registered content refused 409; single-record GET verbatim; unknown id honest 404 | `GET /research/datasets` 200, 5 records, all `PG_SIP_REFERENCE`, splits `{train, holdout}` both present, `integrity_errors: []`; re-tag POST → 409 `"...split tags are frozen at registration..."`; `GET /research/datasets/{id}` 200 verbatim (checksum matches list); unknown id → 404 `"no dataset with id..."` | PASS | `reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-02-datasets-list-200.png`, `UT-J-02-retag-409-refusal.png`, `UT-J-02-dataset-detail-and-404.png` |
| UT-J-03 | Strategy grammar v1 backtests a dataset into a deterministic PnL report | regression | P1 | `POST /research/backtests` (v1, `default`, fixture train dataset) completes; result carries net/gross R+$ aggregates, win rate, max drawdown, n, seeded null baseline, full provenance, register string; identical re-run reproduces a byte-identical report | Job created (200) → polled to `status: "done"`; `aggregates` = `{n:1, gross_r:-0.05, net_r:-0.16000000000001136, gross_usd:-5, net_usd:-16.000000000001137, win_rate:0, max_drawdown_r:0.16000000000001136}`; `null_baseline.aggregates` present (n:99, own R/$/win_rate/drawdown); register verbatim `"simulated — assumed fees/slippage — not indicative of live results"`; provenance = strategy_id `v1`, profile `default`, `config_fingerprint 4d665603569b9dbf`, `null_baseline_seed 1729`, dataset id+checksum. Re-ran the identical POST → new backtest id (`91e27b28...` vs `dffa96bf...`, confirming no silent dedup) but `aggregates` and `null_baseline.aggregates` were byte-identical (`JSON.stringify` equal) | PASS | `reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-03-backtest-rerun-byte-identical.png` |
| UT-J-04 | Every enhancement lands one honest row in the PnL ledger | happy-path | P1 | `GET /research/pnl/ledger` flips from the iter-0 404 baseline to a live 200 carrying the founding row (enhancement id+title, explicit null baseline side, candidate net R+$ +n per split, provenance, timestamp, register, insufficient-sample labels); no REST write surface (POST/DELETE → 405) | `GET /research/pnl/ledger` → 200 (iter-0 baseline was 404, `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-04-research-pnl-ledger-404.png`). Row: `enhancement_id: "founding-baseline-strategy-v1-default"`, `title: "founding baseline — strategy v1 on default"`, `founding: true`, `baseline: null` (explicit, not fabricated zeros); `candidate.train = {net_r:-0.160..., net_usd:-16.0..., n:1, insufficient_sample:true}`, `candidate.holdout = {net_r:0.333..., net_usd:33.34..., n:1, insufficient_sample:true}` (both correctly flagged — `min_sample_size:5`, n=1<5 on both splits); `provenance` = strategy_id `v1`, profile `default`, `config_fingerprint`, and per-split `backtest_id`+`dataset_id`+`dataset_checksum`; `created_utc` timestamp present; top-level `register` verbatim. `POST` → 405 `{"detail":"Method Not Allowed"}`; `DELETE` → 405 identical. `reports/pnl/pnl-history.md` cross-checked (Bash, not browser) — same enhancement id, same net R/$/n values, dd-MM-yyyy date (`03-07-2026`), register verbatim, "insufficient sample (n < 5)" labels on both splits — matches REST exactly | PASS | `reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-04-research-pnl-ledger-200-flip.png`, `UT-J-04-founding-row-honesty.png`, `UT-J-04-write-405-refusal.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-03

