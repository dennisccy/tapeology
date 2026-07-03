# Goal Iteration 4 — UI Test Results (LLM browser-qa pass)

**Phase:** goal-tape_to_profit-iter-4
**Date:** 2026-07-03
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: target journey J-04 fully verified live (404->200 flip, founding-row honesty, no-write leg);
     required-still-passing J-02/J-03 spot-verified live over their REST surface with no regression found. -->

**Overall:** 3/3 tests passed (0 skipped)

Scope note (lean dispatch): this run tested exactly J-02, J-03, J-04 via Chrome MCP. J-01 and
J-08 were explicitly excluded from this pass — a deterministic replay verifies them separately
(`reports/phase-goal-tape_to_profit-iter-4-regression-replay-results.md`, both PASS, evidence at
`reports/qa/goal-tape_to_profit-iter-4-evidence/J-01-verify.png` and `J-08-verify.png`). No
UT-J-01/UT-J-08 rows are duplicated here.

All three journeys tested here are machine-surface (no frontend change this iteration —
`Frontend Present: no`), so "browser" verification followed the technique mandated by the iter-4
spec and lessons.md: navigate Chrome to a backend-origin page (`http://localhost:8301`) and issue
in-page `fetch()` calls via `eval`, rendering the JSON result into the DOM before each screenshot
so the evidence is visually inspectable, not just a log line. No golden replay script was written
for any of the three — `demo_runner.py` supports only `goto`/`click`/`fill` against page elements,
and these journeys have no UI path to click through (per lessons.md: "Machine-surface journeys get
no golden replay script"). All three fall back to LLM browser-qa again next iteration, as expected.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | Historical tape datasets persist and replay byte-identically (train/hold-out registry) | regression | P1 | committed PG_SIP_REFERENCE fixture pair listed with symbol/window/feed/checksum/split; re-tagging already-registered content refused 409; single-record GET verbatim; unknown id honest 404 | `GET /research/datasets` 200, 5 records, all `PG_SIP_REFERENCE`, splits `{train, holdout}` both present, `integrity_errors: []`; re-tag POST → 409 `"...split tags are frozen at registration..."`; `GET /research/datasets/{id}` 200 verbatim (checksum matches list); unknown id → 404 `"no dataset with id..."` | PASS | `reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-02-datasets-list-200.png`, `UT-J-02-retag-409-refusal.png`, `UT-J-02-dataset-detail-and-404.png` |
| UT-J-03 | Strategy grammar v1 backtests a dataset into a deterministic PnL report | regression | P1 | `POST /research/backtests` (v1, `default`, fixture train dataset) completes; result carries net/gross R+$ aggregates, win rate, max drawdown, n, seeded null baseline, full provenance, register string; identical re-run reproduces a byte-identical report | Job created (200) → polled to `status: "done"`; `aggregates` = `{n:1, gross_r:-0.05, net_r:-0.16000000000001136, gross_usd:-5, net_usd:-16.000000000001137, win_rate:0, max_drawdown_r:0.16000000000001136}`; `null_baseline.aggregates` present (n:99, own R/$/win_rate/drawdown); register verbatim `"simulated — assumed fees/slippage — not indicative of live results"`; provenance = strategy_id `v1`, profile `default`, `config_fingerprint 4d665603569b9dbf`, `null_baseline_seed 1729`, dataset id+checksum. Re-ran the identical POST → new backtest id (`91e27b28...` vs `dffa96bf...`, confirming no silent dedup) but `aggregates` and `null_baseline.aggregates` were byte-identical (`JSON.stringify` equal) | PASS | `reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-03-backtest-rerun-byte-identical.png` |
| UT-J-04 | Every enhancement lands one honest row in the PnL ledger | happy-path | P1 | `GET /research/pnl/ledger` flips from the iter-0 404 baseline to a live 200 carrying the founding row (enhancement id+title, explicit null baseline side, candidate net R+$ +n per split, provenance, timestamp, register, insufficient-sample labels); no REST write surface (POST/DELETE → 405) | `GET /research/pnl/ledger` → 200 (iter-0 baseline was 404, `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-04-research-pnl-ledger-404.png`). Row: `enhancement_id: "founding-baseline-strategy-v1-default"`, `title: "founding baseline — strategy v1 on default"`, `founding: true`, `baseline: null` (explicit, not fabricated zeros); `candidate.train = {net_r:-0.160..., net_usd:-16.0..., n:1, insufficient_sample:true}`, `candidate.holdout = {net_r:0.333..., net_usd:33.34..., n:1, insufficient_sample:true}` (both correctly flagged — `min_sample_size:5`, n=1<5 on both splits); `provenance` = strategy_id `v1`, profile `default`, `config_fingerprint`, and per-split `backtest_id`+`dataset_id`+`dataset_checksum`; `created_utc` timestamp present; top-level `register` verbatim. `POST` → 405 `{"detail":"Method Not Allowed"}`; `DELETE` → 405 identical. `reports/pnl/pnl-history.md` cross-checked (Bash, not browser) — same enhancement id, same net R/$/n values, dd-MM-yyyy date (`03-07-2026`), register verbatim, "insufficient sample (n < 5)" labels on both splits — matches REST exactly | PASS | `reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-04-research-pnl-ledger-200-flip.png`, `UT-J-04-founding-row-honesty.png`, `UT-J-04-write-405-refusal.png` |

---

## Passed Tests

### UT-J-02 — Historical tape datasets persist and replay byte-identically (train/hold-out registry)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-02-datasets-list-200.png`, `UT-J-02-retag-409-refusal.png`, `UT-J-02-dataset-detail-and-404.png`

- Navigated Chrome to `http://localhost:8301/research/datasets` — 200, all 5 registered datasets are the committed `PG_SIP_REFERENCE` fixture content, split tags present as both `train` and `holdout`, each record carries `symbol`, `window_start_utc`/`window_end_utc`, `data_feed`, `event_counts`, `checksum`. `integrity_errors: []`.
- In-page `fetch()` POST `/research/datasets` `{source_kind:"reference", split:"holdout"}` (re-tagging the already-registered full reference window, currently `train`, as `holdout`) → **409**, detail: `"this exact tape is already registered as dataset 'dcfcf3cd...' with split 'train' — split tags are frozen at registration, so re-tagging it 'holdout' is refused"`. Confirms the immutable-split-tag acceptance criterion; the refusal did not create or mutate any row (dataset count unchanged on the subsequent list).
- In-page `fetch()` GET `/research/datasets/9396fd5816394236b365f3da51a0bbe1` → 200, verbatim record, checksum matches the list entry exactly. GET `/research/datasets/does-not-exist-12345` → honest 404 (`"no dataset with id 'does-not-exist-12345'"`), not a fabricated/empty record.
- Not independently re-derived in this browser pass (out of HTTP-surface scope, no REST endpoint exists for it): byte-identical engine replay of dataset events, and "watching a live/sim ticker writes no dataset rows." Both are asserted by the backend automated suite per the iteration's Definition of Done ("J-02 ... via full automated suites ... staying green"), which is a separate testing lane from browser QA.

### UT-J-03 — Strategy grammar v1 backtests a dataset into a deterministic PnL report
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-03-backtest-rerun-byte-identical.png`

- In-page `fetch()` POST `/research/backtests` `{dataset_id: "9396fd58...", strategy_id: "v1", profile: "default"}` (the fixture train dataset) → 200, job created; polled `GET /research/backtests/{id}` until `status: "done"`.
- Result carried: per-split `aggregates` (`n`, `gross_r`, `net_r`, `gross_usd`, `net_usd`, `win_rate`, `max_drawdown_r`), a separately computed `null_baseline.aggregates` (seeded random-entry comparator, n:99), the verbatim register string, and full provenance (`strategy_id`, `profile`, `config_fingerprint`, `null_baseline_seed`, dataset id + checksum).
- Re-issued the byte-identical POST body a second time → a **new** backtest id was assigned (proving no silent caching/dedup — every request genuinely runs), but its `aggregates` and `null_baseline.aggregates` were deep-equal (`JSON.stringify` comparison) to the first run's, confirming the deterministic-reproduction acceptance criterion live, not just in the test suite.
- Two additional backtest records were created on the existing fixture dataset as a side effect of this test (ids `dffa96bfd6fc4b27be9e587e5bad65ed`, `91e27b28e7ae42c58b5ee5f57d121744`) — additive-only, mirrors a normal researcher action, does not touch the PnL ledger (only the seeding CLI appends ledger rows) and does not affect any other journey's evidence.

### UT-J-04 — Every enhancement lands one honest row in the PnL ledger
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-04-research-pnl-ledger-200-flip.png`, `UT-J-04-founding-row-honesty.png`, `UT-J-04-write-405-refusal.png`

- **404→200 flip:** navigated to `http://localhost:8301/research/pnl/ledger` → 200 JSON body with one row. The iter-0 baseline for this same path was 404 (`reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-04-research-pnl-ledger-404.png`) — this screenshot is the flip's live counterpart.
- **Founding-row honesty leg:** in-page `fetch()` GET, rendered into the DOM before capture. Row: `enhancement_id: "founding-baseline-strategy-v1-default"`, `title: "founding baseline — strategy v1 on default"`, `founding: true`, `baseline: null` (explicit null — no fabricated zero comparator, matching "founding-row honesty" from the spec). `candidate.train` and `candidate.holdout` each carry `net_r`, `net_usd`, `n` as separate, never-pooled figures; both are `n:1`, both flagged `insufficient_sample: true` against the response's `min_sample_size: 5` — the label logic fired correctly. `provenance` carries `strategy_id: "v1"`, `profile: "default"`, `config_fingerprint`, and per-split `backtest_id` + `dataset_id` + `dataset_checksum`. `created_utc` timestamp present. Top-level `register` is exactly `"simulated — assumed fees/slippage — not indicative of live results"`.
- **No-write leg:** in-page `fetch()` POST `/research/pnl/ledger` → **405** `{"detail":"Method Not Allowed"}`; DELETE → **405**, same body. No handler exists for either verb — confirmed no REST write surface, as required ("no update or delete path anywhere").
- **Cross-surface consistency (Bash, supplementary — not a browser step):** read the committed `reports/pnl/pnl-history.md`. Same enhancement id, same net R/net $/n values on both splits (`-0.16000000000001136`/`-16.000000000001137`/`1` train, `0.3334000000001356`/`33.34000000001356`/`1` holdout), same register string verbatim, "insufficient sample (n < 5)" labels on both rows, appended date rendered `03-07-2026` (dd-MM-yyyy). Matches REST exactly — no divergent computation path observed.
- **Not independently re-verified here:** the MCP `pnl_ledger` tool's byte-identity to REST. MCP is a stdio process (`python -m app.mcp`), not a browser-reachable surface, and the iteration's own Browser testing requirements list only the 404→200 flip, honesty leg, no-write leg, and J-01/J-08 regression — MCP byte-identity is explicitly an "Unit/integration" requirement, owned by `tests/test_mcp_server.py`. Given MCP tools are documented as thin HTTP clients against this same backend, the REST-level verification above already exercises the shared computation path.

---

## Failed Tests

None.

---

## Skipped Tests

None. (J-01 and J-08 were deliberately not executed in this pass per the lean dispatch instructions — see Scope note above — not "skipped" in the failure sense; they are PASS elsewhere.)

---

## Anti-goal spot-checks observed incidentally

- No execution path: no order/broker/ticket language anywhere in any response body inspected.
- No fabricated data: unknown dataset id → explicit 404, never a synthesized record; founding baseline side → explicit `null`, never a fabricated zero.
- Single source of truth: REST ledger and the committed markdown render carry identical enhancement id, R/$, n, and register values with no divergence.
- No train/hold-out pooling: `candidate.train` and `candidate.holdout` are always separate keys in every payload inspected; no combined/averaged figure appeared anywhere.

---

## Environment

- **Backend URL (exercised in this pass):** http://localhost:8301
- **Frontend URL:** http://localhost:3301 (not exercised — `Frontend Present: no` this iteration; no UI changed)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), in-page `fetch()` via `eval` from a backend-origin page (machine-surface verification technique per lessons.md)
- **Test Date:** 2026-07-03
- **Evidence directory:** `reports/qa/goal-tape_to_profit-iter-4-evidence/`
- **Golden replay scripts:** none written for J-02/J-03/J-04 — no UI path exists for `demo_runner.py`'s `goto`/`click`/`fill` model to drive; these three fall back to LLM browser-qa again next iteration by design.
