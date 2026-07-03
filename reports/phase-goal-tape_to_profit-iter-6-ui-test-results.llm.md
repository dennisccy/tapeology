# Goal Iteration 6 — UI/Browser Test Results

**Phase:** goal-tape_to_profit-iter-6
**Date:** 2026-07-03
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. -->

**Overall:** 4/4 tests passed (0 skipped)

Scope this run (lean-mode dispatch): **J-02, J-03, J-04, J-06** — all four are backend/machine-surface
journeys with no frontend UI (Frontend Present: no for iter-6; the `/performance` panel that
renders the new profile row is J-05's concern and is explicitly out of scope this run, verified
separately by golden replay along with J-01 and J-08). Verified via Chrome MCP **in-page
`fetch()`** from a backend-origin page (`http://localhost:8301/docs`), per the iter-6 spec's
"Machine-surface regression lane" note — `demo_runner.py`'s golden-replay format is
goto/click/fill only and cannot express the POST-heavy flows these journeys require, so **no
golden replay scripts were written** for J-02/J-03/J-04/J-06 this run (consistent with the spec's
own guidance that their durable regression lane is the backend suite, not the replay lane).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | Historical tape datasets persist and replay byte-identically | regression | P1 | Record dataset (symbol/window/feed/checksum stored); re-tag attempt refused 409; list reflects it; watching a sim ticker writes no rows | Recorded new dataset (7th row), checksum+metadata stored; re-tag same content → 409 with honest re-tag message; list count 6→7, new row present verbatim; watch/unwatch SIM-BUYER left dataset count unchanged (7→7→7) | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-result.png`, `UT-J-02-ambient-check.png` |
| UT-J-03 | Strategy grammar v1 backtests a dataset into a deterministic PnL report | regression | P1 | POST starts job, polls to done; report has trades + net/gross R&$, win rate, max drawdown, n, null baseline, full provenance; identical re-run is byte-identical; no broker code | POST→`queued`→`done`; aggregates carry gross_r/net_r/gross_usd/net_usd/win_rate/max_drawdown_r/n; null_baseline present (seed 1729); provenance stamped (dataset id+checksum, strategy_id, profile, fingerprint); re-run produced a different backtest id with byte-identical trades/aggregates/null_baseline; both runs appear in the list; grep found no broker/order/paper-trading code (only a comment documenting the anti-goal) | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-03-result.png` |
| UT-J-04 | Every enhancement lands one honest row in the PnL ledger | regression | P1 | Ledger shows founding row (baseline null, train+holdout separate, n, provenance, timestamp); no update/delete path; markdown regen is a byte-level no-op; REST/markdown numbers match | Founding row present: train net_r -0.16000000000001136 (n=1, insufficient sample), holdout net_r 0.3334000000001356 (n=1, insufficient sample), full provenance + timestamp; DELETE/PUT/POST all → 405; `python -m app.research.pnl_history` regen produced byte-identical sha256 before/after (`git diff` empty); markdown numbers match REST exactly | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-04-result.png` |
| UT-J-06 | Indicator profiles are versioned; the default stays byte-identical | smoke | P1 | `/research/profiles` lists default+candidate; backtests under both profiles differ only legitimately; unknown profile → honest 422; default fingerprint unchanged, candidate fingerprint distinct | `GET /research/profiles` → `default` (frozen) + `candidate-faster-warmup` (based_on default, overrides `warmup_min_events:30`); champion still `v1`/`default`; default holdout backtest: fingerprint `4d665603569b9dbf`, net_r `+0.3334000000001356` (exact pinned match); candidate holdout backtest: fingerprint `8c2c0fbf978228e3`, net_r `-0.1728000000000723` (exact pinned match) — same setup/direction (`trend_continuation`/`long`), materially different outcome (win_rate 1.0→0.0); candidate re-run byte-identical (deterministic); unknown profile → 422 `"unknown profile 'nonexistent-profile-xyz' — the registered profiles are ['default', 'candidate-faster-warmup']"` | PASS | `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-06-result.png` |

---

## Passed Tests

### UT-J-02 — Historical tape datasets persist and replay byte-identically
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-result.png`, `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-ambient-check.png`

- `GET /research/datasets` before: 6 datasets (all with symbol, UTC window, feed, event_counts, checksum, split — pre-existing from prior iterations).
- `POST /research/datasets` with a fresh, previously-unused fixture sub-window (`source_kind: reference`, `split: train`, `start: 2026-06-09T17:03:00Z`, `end: 2026-06-09T17:03:15Z`) → `200`, new dataset `cb493e80dd574a7eaaf904726698649a` (232 trades, 272 quotes, checksum `b00a6dc9...`) — proves the committed reference fixture records keyless.
- Immediate re-POST of the **exact same window** under `split: holdout` (the re-tag attempt) → `409` with an honest, explicit message: *"this exact tape is already registered as dataset 'cb493e80dd574a7eaaf904726698649a' with split 'train' — split tags are frozen at registration, so re-tagging it 'holdout' is refused"*.
- `GET /research/datasets` after: count 6→7, new row present verbatim (same id/checksum/metadata echoed back).
- `GET /research/datasets/does-not-exist-xyz` → `404` (bonus check, honest not-found).
- **No-ambient-recording check** (anti-goal "Persistence stays scoped"): `POST /watch/SIM-BUYER` → `200 watching`; waited 2.5s; `GET /tape/SIM-BUYER/state` → `200` (live stream, warming up); dataset count during watch stayed at 7; `DELETE /watch/SIM-BUYER` → `200`; dataset count after unwatch stayed at 7. Watching a sim ticker wrote **zero** dataset rows.
- **Not independently re-verified live** (covered by the automated suite, not re-triggered here to avoid corrupting shared state): checksum-tamper → explicit integrity error; byte-identical replay of the stored dataset vs. the original source stream (an internal engine-level comparison with no REST surface to drive from the browser). Indirect evidence: J-03/J-06 below both show two independent backtest runs against the same dataset reproducing byte-identical trades/aggregates, which is only possible if the dataset replays deterministically.

### UT-J-03 — Strategy grammar v1 backtests a dataset into a deterministic PnL report
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-03-result.png`

- `POST /research/backtests` (`dataset_id: 9396fd58...`, `strategy_id: v1`, `profile: default`) → `200`, job created `queued`, polled to `done`.
- Report `register`: *"simulated — assumed fees/slippage — not indicative of live results"*.
- `aggregates` carries all required fields: `n`, `gross_r`, `net_r`, `gross_usd`, `net_usd`, `win_rate`, `max_drawdown_r` (values: n=1, gross_r=-0.05, net_r=-0.16000000000001136, gross_usd=-5, net_usd=-16.000000000001137, win_rate=0, max_drawdown_r=0.16000000000001136).
- `null_baseline` present with recorded seed `1729` (seeded random-entry baseline beside the strategy result).
- Full provenance stamped: dataset id + checksum, `strategy_id`, `profile`, `config_fingerprint` (`4d665603569b9dbf`).
- Identical re-run (same dataset/strategy/profile) produced a **different** backtest id but **byte-identical** `trades`, `aggregates`, and `null_baseline` (string-compared) — determinism confirmed.
- Both runs appear in `GET /research/backtests`.
- Supplementary grep (`apps/backend/app`, excluding tests) for broker/order/paper-trading code: only one hit, a comment in `providers/adapters/alpaca.py` explicitly documenting the anti-goal ("integrates no execution/brokerage capability") — no actual broker/order/account code exists.

### UT-J-04 — Every enhancement lands one honest row in the PnL ledger
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-04-result.png`

- `GET /research/pnl/ledger` → `register` = simulated caveat string; `min_sample_size` = 5; 1 row (the founding baseline, no promotions yet — matches J-06's out-of-scope guarantee that no ledger row was appended this iteration).
- Founding row: `enhancement_id: founding-baseline-strategy-v1-default`, `baseline: null` (no prior incumbent, never fabricated), `train: {net_r: -0.16000000000001136, net_usd: -16.000000000001137, n: 1, insufficient_sample: true}`, `holdout: {net_r: 0.3334000000001356, net_usd: 33.34000000001356, n: 1, insufficient_sample: true}` — train and holdout kept separate, never pooled; both correctly labeled "insufficient sample" since n=1 < min_sample_size=5.
- Full provenance (strategy/profile/fingerprint + per-split backtest id, dataset id, dataset checksum) and `created_utc` timestamp present.
- **No write surface:** `DELETE`, `PUT`, and `POST` to `/research/pnl/ledger` all → `405` (no handler exists — matches "no update or delete path").
- Regenerated the markdown via `python -m app.research.pnl_history`: sha256 of `reports/pnl/pnl-history.md` identical before and after (`4ad09e96f4e2ba...`), `git diff --stat` empty — a byte-level no-op, confirming the markdown is a pure render.
- Read the regenerated markdown directly: numbers match the REST payload exactly (train `-0.16000000000001136`/`-16.000000000001137`, holdout `0.3334000000001356`/`33.34000000001356`, fingerprint `4d665603569b9dbf`, same backtest/dataset/checksum ids), and the date is rendered `03-07-2026` (dd-MM-yyyy, per the foundation invariant).

### UT-J-06 — Indicator profiles are versioned; the default stays byte-identical
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-06-result.png`

- `GET /research/profiles` → `profiles: [{id: default, frozen: true, is_default: true}, {id: candidate-faster-warmup, frozen: false, is_default: false, based_on: default, overrides: {warmup_min_events: 30}}]`; `champion: {strategy_id: v1, profile: default}` — unmoved.
- Ran the same fixture holdout dataset (`aa749b668553473294e7ca5a9caa69d6`) as a backtest under **both** profiles:
  - `default` → `done`, `config_fingerprint: 4d665603569b9dbf` (the pinned, unchanged default fingerprint), `net_r: 0.3334000000001356` — this **exactly** matches the founding PnL-ledger row's holdout leg read independently in UT-J-04, i.e. an independent fresh run reproduces the archived-era number exactly.
  - `candidate-faster-warmup` → `done`, `config_fingerprint: 8c2c0fbf978228e3` (distinct, pinned candidate fingerprint), `net_r: -0.1728000000000723`.
  - Both trades share the same `setup_type` (`trend_continuation`) and `direction` (`long`) — the candidate's earlier warmup arms the same setup but the outcome flips from a clean winner (`win_rate: 1.0`) to a loss (`win_rate: 0.0`) — a real, legitimate behavioral difference, not a metadata relabel.
  - Re-ran the candidate a second time: aggregates and per-trade summary byte-identical to the first candidate run (different backtest id) — individually deterministic.
- Unknown profile: `POST /research/backtests` with `profile: nonexistent-profile-xyz` → `422`, `detail: "unknown profile 'nonexistent-profile-xyz' — the registered profiles are ['default', 'candidate-faster-warmup']"` — an honest refusal listing the registered profiles, never a silent fallback.
- Supplementary source check: `grep -rn "resolved_for_profile(" app/` (excluding tests) shows exactly two call sites, both inside `app/research/backtests.py` (the backtest runner) plus the method's own definition in `config.py` — no cockpit/live/archived-era path calls it. Read `Config.resolved_for_profile`: `default` returns `self` unchanged (the identical object — the strongest byte-identical guarantee); a candidate returns a fresh `dataclasses.replace(self, **overrides)` (the shared `CONFIG` singleton is never mutated); an unregistered id returns `None` (never a silent default fallback).
- **Not independently re-verified live** (covered by the automated suite): the full pinned-fixture equivalence assertion in `tests/test_profile_equivalence.py` (byte-identical state/confidence/features/history against a pre-profile golden snapshot) — no REST surface exposes that internal comparison for a browser check to drive; the fingerprint + net-R matches above are strong indirect evidence of the same guarantee.

---

## Failed Tests

None.

---

## Skipped Tests

None. Both the frontend precondition and Chrome MCP were available; all four in-scope journeys were exercised.

**Note on MCP-tool cross-checks:** J-02/J-03/J-04's acceptance text calls for comparing REST output against the MCP `datasets`/`backtests`/`pnl_ledger` tools. This agent's direct `mcp__tapeology__*` tool access is wired to the canonical default port `http://localhost:8000`, but this goal-mode session's backend runs on the session-offset port `8301` (confirmed nothing listens on 8000 in this environment). Calling `mcp__tapeology__datasets` correctly returned an explicit connection error rather than fabricated data — itself consistent with the read-only-MCP anti-goal, but it means I could not diff MCP JSON against this session's REST payloads directly. This is an environment/session-topology fact, not a product defect (the byte-identical MCP↔REST proxy behavior is J-01's own acceptance test, explicitly out of scope this run and verified separately by golden replay). All REST-surface behavior for J-02/J-03/J-04/J-06 was verified directly and thoroughly.

---

## Golden replay scripts

**None written this run.** J-02, J-03, J-04, and J-06 are all backend/machine-surface journeys
driven by `POST` + polling `GET` sequences (dataset recording, backtest jobs, ledger reads,
profile validation). `demo_runner.py`'s replay schema supports only `goto` / `click` / `fill`
actions and cannot express a `POST` body or a fetch-based assertion, so none of these four
journeys has a goto/click/fill equivalent to record. This matches the iter-6 spec's own
"Machine-surface regression lane" note: their durable regression lane is the backend test suite,
not the golden-replay lane. (J-01/J-05/J-08 already have golden scripts from prior iterations and
were correctly excluded from this run's browser QA scope.)

---

## Environment

- **Frontend URL:** http://localhost:3301 (not exercised — Frontend Present: no for iter-6; no UI surface changed)
- **Backend URL:** http://localhost:8301 (session-offset port; used as the same-origin page for in-page `fetch()` — `/docs` Swagger UI)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless
- **Test Date:** 2026-07-03
- **Evidence directory:** `reports/qa/goal-tape_to_profit-iter-6-evidence/`
