# Phase goal-tape_to_profit-iter-5 — UI Test Results (LLM browser-qa lane)

**Phase:** goal-tape_to_profit-iter-5
**Date:** 2026-07-03
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 4/4 tests passed (0 skipped)

Scope note: this lane covers J-02, J-03, J-04, J-05 only, per the lean-mode dispatch. J-01
and J-08 are covered separately by deterministic golden-script replay
(`reports/phase-goal-tape_to_profit-iter-5-regression-replay-results.md`, PASS 2/2) and are
NOT re-tested here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | Historical tape datasets persist and replay byte-identically (train/hold-out registry) | regression | P1 | Record via `POST /research/datasets` succeeds keyless; identical-content re-record and re-tag are refused 409; list/detail serve stored metadata verbatim; unknown id 404; dataset replay is byte-identical | Recorded a fresh train-split dataset via genuine in-page `fetch()` POST (id `e09e8ae6b1f84a3b8545d1f426917cfd`, symbol PG, window 17:02:00–17:02:30Z, feed sip, 229 trades/557 quotes/786 total events, 64-char checksum) → 200; identical re-POST (same split, same content) → 409 "this exact tape is already registered ... frozen at registration"; re-tag attempt (same content, split changed to holdout) → 409 "split tags are frozen at registration, so re-tagging it 'holdout' is refused"; `GET` list and `GET` detail byte-identical to the create response; unknown id → 404. Targeted independent re-run `pytest tests/test_datasets_api.py` (part of a 57-test batch, see UT-J-03) — 0 failed, exit 0. Byte-identical-replay-vs-source-stream is an internal engine assertion with no REST surface; covered by the automated suite (re-run below), not separately re-derived in-browser | PASS | `reports/qa/goal-tape_to_profit-iter-5-evidence/J-02-record-detail-200.png` |
| UT-J-03 | Strategy grammar v1 backtests a dataset into a deterministic PnL report | regression | P1 | `POST /research/backtests` (v1, default, fixture dataset) completes with net/gross R+$ aggregates, win rate, max drawdown, n, seeded null baseline, full provenance, register; identical re-run reproduces a byte-identical report | POST against the J-02 dataset above created a job (`status: "queued"`), polled via `GET /research/backtests/{id}` to `"done"`; `aggregates = {n:1, gross_r:0.10166666666667457, net_r:-0.001666666666674561, gross_usd:10.166666666667457, net_usd:-0.1666666666674561, win_rate:0, max_drawdown_r:0.001666666666674561}`; `null_baseline.aggregates` present and independent (n:99, own R/$/win_rate/drawdown); `register` verbatim "simulated — assumed fees/slippage — not indicative of live results"; provenance = strategy `v1` · profile `default` · `config_fingerprint 4d665603569b9dbf` · dataset id+checksum matching the just-recorded dataset. Re-ran the identical POST → new backtest id (`ea810a43...` vs `b96c7630...`, confirming no silent dedup) but `aggregates` and `null_baseline.aggregates` were byte-identical (`JSON.stringify` equal). Targeted independent re-run `pytest tests/test_backtests_api.py` (same batch) — 0 failed, exit 0 | PASS | `reports/qa/goal-tape_to_profit-iter-5-evidence/J-03-backtest-done-report.png` |
| UT-J-04 | Every enhancement lands one honest row in the PnL ledger | regression | P1 | `GET /research/pnl/ledger` carries the founding row (enhancement id+title, explicit null baseline, candidate net R+$+n per split, provenance, timestamp, register, insufficient-sample labels); no write surface (`POST`/`DELETE` → 405); rendered markdown matches REST | `GET /research/pnl/ledger` → 200, 1 row: `enhancement_id: "founding-baseline-strategy-v1-default"`, `title: "founding baseline — strategy v1 on default"`, `founding: true`, `baseline: null` (explicit — never a fabricated 0); `candidate.train = {net_r:-0.16000000000001136, net_usd:-16.000000000001137, n:1, insufficient_sample:true}`; `candidate.holdout = {net_r:0.3334000000001356, net_usd:33.34000000001356, n:1, insufficient_sample:true}` (both correctly flagged — `min_sample_size:5`, n=1<5 on both splits); `register` verbatim. `POST /research/pnl/ledger` → 405; `DELETE /research/pnl/ledger` → 405 (no write/update/delete path exists). `reports/pnl/pnl-history.md` cross-checked (Bash, not browser) — same enhancement id, same net R/$/n values, dd-MM-yyyy date (`03-07-2026`), register verbatim, "insufficient sample (n < 5)" on both splits — matches REST exactly | PASS | `reports/qa/goal-tape_to_profit-iter-5-evidence/J-04-ledger-founding-row-200.png` |
| UT-J-05 | The /performance page reports PnL per enhancement honestly | happy-path | P1 | `/performance` reached from the top-bar Performance link; ledger renders `GET /research/pnl/ledger` verbatim (every $ beside its R and its n, register visible, train/hold-out columns separate, "insufficient sample" on both founding-row splits, explicit founding-baseline marker never 0); champion summary equals `GET /research/profiles`; nav reads Cockpit/Journal/Studies/Performance on every page; `GET /meta/ui-routes` includes `/performance`; dark cockpit design language | From `/`, the top bar showed exactly 4 links (Cockpit active, Journal, Studies, Performance — rendered from `GET /meta/ui-routes`). Clicked "Performance" → URL became `/performance`, Performance link `aria-current="page"`. Ran a live in-page `fetch()` comparison of the rendered DOM text against `GET /research/pnl/ledger` + `GET /research/profiles` from inside the actual page: **24/24 checks true** — register verbatim; ledger row title + enhancement id; candidate train/hold-out net R, net $, n (full precision: `-0.16000000000001136`, `-16.000000000001137`, `0.3334000000001356`, `33.34000000001356`); "insufficient sample (n < 5)" on both splits; "no prior incumbent" founding marker (baseline explicitly `null`, no fabricated zero anywhere in the row); full provenance strings visible (strategy id, profile, config fingerprint, per-split backtest id, dataset id, dataset checksum); `champion-strategy`/`champion-profile` testids equal `v1`/`default` from `GET /research/profiles`; profile-registry row shows `default` / frozen / default; date rendered `dd-MM-yyyy` ("Appended 03-07-2026"). Spot-checked the 4-link nav bar on `/journal` and `/studies` — both showed the identical 4 links including Performance. Independently re-fetched `GET /meta/ui-routes`: 5 entries, 4 `nav:true` (`/`, `/journal`, `/studies`, `/performance`), `/performance` labeled "Performance" — matches the rendered links exactly. Page uses the established dark slate-950/slate-900/emerald/amber cockpit language, `font-mono` numerics, consistent with `/journal` and `/studies`. Wrote and independently replayed the golden script `runs/goal-session-tape_to_profit/journey-scripts/J-05.json` via `demo_runner.py --mode verify`: **1/1 PASS, all expects held** | PASS | `reports/qa/goal-tape_to_profit-iter-5-evidence/J-05-01-cockpit-4links.png`, `J-05-02-performance-page.png`, `J-05-03-studies-4link-navspotcheck.png` |

---

## Passed Tests

### UT-J-02 — Historical tape datasets persist and replay byte-identically
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tape_to_profit-iter-5-evidence/J-02-record-detail-200.png`
- Record/list/detail/re-record-refusal/re-tag-refusal/unknown-id-404 all exercised via genuine browser `fetch()` calls against the live harness backend (`localhost:8301`), not curl/pytest.
- No change to `datasets.py` this iteration (confirmed zero-diff by the dev handoff); this run is a live regression re-check, not first-time discovery.

### UT-J-03 — Strategy grammar v1 backtests a dataset into a deterministic PnL report
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tape_to_profit-iter-5-evidence/J-03-backtest-done-report.png`
- Full aggregate shape (net/gross R+$, win rate, max drawdown, n) and an independent seeded null baseline confirmed present and populated.
- Determinism proven live: two identical POSTs produce different backtest ids (no silent dedup) but byte-identical `aggregates` and `null_baseline.aggregates`.

### UT-J-04 — Every enhancement lands one honest row in the PnL ledger
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tape_to_profit-iter-5-evidence/J-04-ledger-founding-row-200.png`
- Founding row values match the iter spec's pinned acceptance figures exactly (train net R `-0.16000000000001136` / net $ `-16.000000000001137`; hold-out net R `0.3334000000001356` / net $ `33.34000000001356`; both n=1, both "insufficient sample").
- Write surface confirmed absent: `POST` and `DELETE` both refused with 405.
- `reports/pnl/pnl-history.md` (markdown surface) cross-checked byte-for-byte consistent with the REST surface — single source of truth holds across surfaces.

### UT-J-05 — The /performance page reports PnL per enhancement honestly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tape_to_profit-iter-5-evidence/J-05-01-cockpit-4links.png`, `J-05-02-performance-page.png`, `J-05-03-studies-4link-navspotcheck.png`
- This is the iteration's new browser-facing capability: the fourth top-bar link and the `/performance` page, both reached and read through live Chrome MCP interaction (navigate, click, in-page `fetch()`, DOM assertions) — not a static read of source.
- Page performs no arithmetic anywhere: every asserted value is a raw string match against the API's own full-precision text, satisfying the "value shown equals API value exactly" acceptance line.
- Champion is read only from `GET /research/profiles`, never inferred from ledger provenance — verified by independently fetching both endpoints and comparing.
- No hardcoded route list found: the 4-link nav on `/`, `/journal`, `/studies` all trace to the same `GET /meta/ui-routes` payload, confirmed by direct endpoint fetch.
- Golden replay script `runs/goal-session-tape_to_profit/journey-scripts/J-05.json` rewritten from this run's verified steps and independently replayed green via `demo_runner.py --mode verify --journeys J-05` (1/1 PASS) before being left in place for future iterations' fast regression lane.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Supplementary independent verification (beyond Chrome MCP)

Not part of the 4 required journeys' pass/fail determination, but run to strengthen confidence
per the iteration's "verify-and-complete" resume framing (dev-handoff claims are unverified
until independently reproduced):

- `pytest tests/test_meta_routes.py tests/test_profiles_api.py tests/test_mcp_server.py tests/test_datasets_api.py tests/test_backtests_api.py -q` → **57 passed, 0 failed, exit 0** (targeted re-run of every backend test file touching this iteration's changed modules plus the J-02/J-03 machine-surface journeys).

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-03
- **Evidence directory:** `reports/qa/goal-tape_to_profit-iter-5-evidence/`
