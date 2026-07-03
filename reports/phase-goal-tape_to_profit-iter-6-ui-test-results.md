# UI Test Results (merged)

**Date:** 2026-07-03
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | A read-only MCP server exposes the product over the canonical API | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-6-evidence/J-01-verify.png |
| UT-J-05 | The /performance page reports PnL per enhancement honestly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-6-evidence/J-05-verify.png |
| UT-J-08 | The existing product is unchanged (regression sentinel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-6-evidence/J-08-verify.png |
| UT-J-02 | Historical tape datasets persist and replay byte-identically | regression | P1 | Record dataset (symbol/window/feed/checksum stored); re-tag attempt refused 409; list reflects it; watching a sim ticker writes no rows | Recorded new dataset (7th row), checksum+metadata stored; re-tag same content → 409 with honest re-tag message; list count 6→7, new row present verbatim; watch/unwatch SIM-BUYER left dataset count unchanged (7→7→7) | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-result.png`, `UT-J-02-ambient-check.png` |
| UT-J-03 | Strategy grammar v1 backtests a dataset into a deterministic PnL report | regression | P1 | POST starts job, polls to done; report has trades + net/gross R&$, win rate, max drawdown, n, null baseline, full provenance; identical re-run is byte-identical; no broker code | POST→`queued`→`done`; aggregates carry gross_r/net_r/gross_usd/net_usd/win_rate/max_drawdown_r/n; null_baseline present (seed 1729); provenance stamped (dataset id+checksum, strategy_id, profile, fingerprint); re-run produced a different backtest id with byte-identical trades/aggregates/null_baseline; both runs appear in the list; grep found no broker/order/paper-trading code (only a comment documenting the anti-goal) | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-03-result.png` |
| UT-J-04 | Every enhancement lands one honest row in the PnL ledger | regression | P1 | Ledger shows founding row (baseline null, train+holdout separate, n, provenance, timestamp); no update/delete path; markdown regen is a byte-level no-op; REST/markdown numbers match | Founding row present: train net_r -0.16000000000001136 (n=1, insufficient sample), holdout net_r 0.3334000000001356 (n=1, insufficient sample), full provenance + timestamp; DELETE/PUT/POST all → 405; `python -m app.research.pnl_history` regen produced byte-identical sha256 before/after (`git diff` empty); markdown numbers match REST exactly | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-04-result.png` |
| UT-J-06 | Indicator profiles are versioned; the default stays byte-identical | smoke | P1 | `/research/profiles` lists default+candidate; backtests under both profiles differ only legitimately; unknown profile → honest 422; default fingerprint unchanged, candidate fingerprint distinct | `GET /research/profiles` → `default` (frozen) + `candidate-faster-warmup` (based_on default, overrides `warmup_min_events:30`); champion still `v1`/`default`; default holdout backtest: fingerprint `4d665603569b9dbf`, net_r `+0.3334000000001356` (exact pinned match); candidate holdout backtest: fingerprint `8c2c0fbf978228e3`, net_r `-0.1728000000000723` (exact pinned match) — same setup/direction (`trend_continuation`/`long`), materially different outcome (win_rate 1.0→0.0); candidate re-run byte-identical (deterministic); unknown profile → 422 `"unknown profile 'nonexistent-profile-xyz' — the registered profiles are ['default', 'candidate-faster-warmup']"` | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-06-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-03

