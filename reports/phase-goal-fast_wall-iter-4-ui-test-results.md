# UI Test Results (merged)

**Date:** 2026-07-17
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/17 journeys passed (15 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | The foundation is unchanged (regression sentinel) | regression (automated + browser-verifiable) | P1 | Full suite green; equivalence + fingerprint pinned; cockpit/journal/studies/performance/structure era-1–5B behaviors unchanged | Automated portion strongly evidenced (full suite 1489/1489 green, `test_profile_equivalence.py` 15/15, `config_fingerprint` independently confirmed = `4d665603569b9dbf` via direct Python import). **The browser portion was not verified this run** (Chrome MCP unavailable) — I could neither confirm nor refute the golden-replay lane's flagged "possible regression." See Notable Finding #3: a pre-existing screenshot in the evidence directory strongly suggests that flag was caused by the *standard* backend (port 8301) being unreachable at replay time (an infrastructure/service-availability issue), not an actual product regression — but this is circumstantial, not a re-confirmation | SKIP | `reports/qa/goal-fast_wall-iter-4-evidence/J-07-verify.png` (pre-existing, not produced by this run — see Notable Finding #3) |
| UT-01 | Not-computed panel loads (cold) | smoke | P1 | Panel renders with headline/detail/enabled button, no progress/error/table | Not executed — Chrome MCP unavailable. Supplementary: `curl http://localhost:8391/research/edge-report` on a freshly-seeded scoped backend (`datasets_j03`, cold cache) returned exactly `{"status":"not_computed","detail":"The 3-way strategy-comparison sweep has not been run for the current dataset registry and configuration. It never runs automatically on a GET -- an operator must trigger the compute.","dataset_count":1,"register":"simulated — assumed fees/slippage — not indicative of live results","compute":null}` — the backend payload driving this panel is confirmed correct, but the rendered button/DOM was never visually verified | SKIP | none (no screenshot) |
| UT-02 | Full compute lifecycle | happy-path | P1 | Click → running → report or honest empty state, no reload | Not executed — Chrome MCP unavailable. Supplementary: triggered the same lifecycle via `curl -X POST .../research/edge-report/compute` on the scoped backend; got `state:"running"` then (near-instantly, as the test plan itself predicts for `datasets_j03`) `state:"done"`; final `GET /research/edge-report` returned `{"train":{"cells":[]},"holdout":{"cells":[]},"surviving_train_cells":[]}` — the honest empty-cells outcome (b) the test plan calls a valid pass. Backend mechanics confirmed; the actual button/progress-line/panel-swap UI was never seen | SKIP | none (no screenshot) |
| UT-03 | Button blocks second trigger | validation | P2 | Second click while running has no effect | Not executed — Chrome MCP unavailable. A manual curl-based double-POST was attempted but was inconclusive by design: the fixture resolves in ~1ms, so both sequential requests landed after the first had already reached a terminal state (each got a *different* job id, which is correct behavior for two genuinely sequential triggers, not evidence of a single-flight defect). The authoritative check is `tests/test_edge_report_compute.py::test_second_trigger_while_running_returns_the_same_job_started_false` (TC-2), which uses `threading.Event` pairs to deterministically hold a fake compute mid-flight rather than relying on wall-clock timing — this test passed as part of the full suite (see Automated Evidence) | SKIP | none (no screenshot) |
| UT-04 | Progress line format | happy-path | P2 | `{n} / {n} backtests` pattern, no "from cache" suffix yet | Not executed — Chrome MCP unavailable | SKIP | none (no screenshot) |
| UT-05 | Failed compute shows exact error | error | P2 | Red error line with exact backend message, "Retry compute" enabled | Not executed — Chrome MCP unavailable. Supplementary: reproduced the corrupted-fixture scenario via curl (see Notable Finding #1 below) and confirmed the **exact** error string a real click would surface: `"1 dataset file(s) failed integrity verification (['5232fa672b7b4077a5117d34b14c807d.json']) — the report stops with nothing written"`. **Important:** this investigation also surfaced a likely defect in the test plan's own sub-recipe ordering — see Notable Finding #1 | SKIP | none (no screenshot) |
| UT-06 | Unreachable backend at click | error | P2 | Distinct trigger-error line, button returns to idle | Not executed — Chrome MCP unavailable. This test is **pure client-side fetch error-handling** (confirmed by reading `apps/frontend/lib/api.ts`'s `triggerEdgeReportCompute`, which catches a network failure and returns `error: "Backend unreachable — is the API running?"`); curl cannot exercise this path at all, so there is no meaningful non-browser substitute for this one | SKIP | none (no screenshot) |
| UT-07 | Reload mid-job resumes state | happy-path | P1 | Reload never shows plain idle button while a job is in flight or after it finished | Not executed — Chrome MCP unavailable | SKIP | none (no screenshot) |
| UT-08 | Reload after failure resumes state | happy-path | P2 | Reload shows the same "Retry compute" + error, no click needed | Not executed — Chrome MCP unavailable. Also depends on UT-05's sub-recipe, which this run's investigation found is likely mis-ordered (Notable Finding #1) | SKIP | none (no screenshot) |
| UT-09 | J-01 not-computed render frozen | regression | P1 | Exact headline/detail text unchanged, `compute:null` on a truly cold instance | Not executed for the rendered DOM — Chrome MCP unavailable. Supplementary: curl-confirmed the backend payload text is byte-exact to the test's expected strings (see UT-01's curl evidence, same payload) | SKIP | none (no screenshot) |
| UT-10 | Other sections unaffected (J-07) | regression | P1 | All 6 section headings present, no crashed/blank sections | Not executed for a real rendered view — Chrome MCP unavailable. Supplementary: fetched the raw SSR HTML via curl (`curl http://localhost:3391/structure`) and confirmed all 6 expected headings are textually present in the static shell: Tradable Map, Case Studies, Edge Report, Fetch from Yahoo Finance, Registry, Comparison. **Caveat:** the Edge Report section's dynamic content is client-fetched after hydration (confirmed it renders only the `edge-report-loading` skeleton in the raw curl HTML), so this SSR check can only prove the static shell/headings exist — it cannot prove per-section runtime behavior or absence of a client-side crash | SKIP | none (no screenshot) |
| UT-11 | Retry succeeds after fix | happy-path | P3 | Retry recomputes against fixed data, reaches report/empty state, not the same error | Not executed — Chrome MCP unavailable. Also see Notable Finding #2: the test plan's own restore step restarts the backend, and this iteration's job state is explicitly documented as process-scoped/lost-on-restart (`docs/goal.md` Product Shape: "Job state is process-scoped bookkeeping (honestly lost on restart...)"), which appears to contradict the test plan's step-1 prediction that "Retry compute" + the old error survive that restart — flagged for the test plan's own maintainers, not a product defect | SKIP | none (no screenshot) |
| UT-12 | Feature discoverability | ux | P2 | Button self-explanatory, reachable by scrolling only | Not executed — Chrome MCP unavailable | SKIP | none (no screenshot) |
| UT-J-01 | Stop the bleeding — GET never computes | regression (browser-verifiable) | P1 | Cold cache → not-computed payload, zero sweep calls from GET; warm cache byte-identical; browser renders frozen texts | Backend/API portion strongly evidenced: curl-confirmed exact not-computed payload shape on a cold scoped instance (see UT-01); full pytest suite includes the `edge_report`/`edge_report_api`/`edge_report_cache` family (118 tests total, 0 failures) which covers the compute-spy and determinism assertions. Browser-rendered confirmation ("the warm scoped-fixture cache still renders 'No edge-report cells yet.' verbatim in the browser") was **not** performed — Chrome MCP unavailable | SKIP | none (no screenshot); supplementary curl evidence inline above |
| UT-J-02 | Stores stop re-reading — verified-content caches + durable index | regression (keyless; automated — not browser-tagged in docs/goal.md) | P1 | Zero-re-read spy tests pass on both stores; tamper still detected; racy-write guard holds; durable index survives simulated restart | Full pytest suite: `test_bars.py`+`test_bars_api.py` = 46 tests, `test_datasets.py`+`test_datasets_api.py` = 37 tests, `test_dataset_index.py` = 7 tests — **all passing, 0 failures** (part of the 1489/1489 green full-suite run, JUnit-XML-verified; see Automated Evidence). This journey carries no browser-verifiable clause in `docs/goal.md` (tagged "Keyless; automated"), so this constitutes its actual, complete verification method — not a fallback | **PASS** | `runs/pytest full suite: 1489 total, 0 failures, 0 errors, 7 skipped (all TAPEOLOGY_LIVE_INTEGRATION-gated)` |
| UT-J-03 | The arm memo — per-tick levels recompute becomes ~100 memo hits | regression (keyless; automated — not browser-tagged) | P1 | Memoized structure_tape/structure_tape_map byte-identical to fresh; counting spy proves batched `compute_levels` calls; guard tests unmodified | Full pytest suite: `test_levels.py`+`test_levels_api.py` = 41 tests, `test_tradability.py`+`test_tradability_api.py` = 34 tests, `test_backtests.py`+`test_backtests_api.py` = 75 tests (includes the source-introspection guard tests at `test_backtests.py:1500-1508`/`932-943`) — **all passing, 0 failures**. No browser-verifiable clause for this journey either | **PASS** | same full-suite run as UT-J-02 |
| UT-J-04 | The operator-run compute — button, background job, CLI warmer | regression (this iteration's target; browser-verifiable) | P1 | Single-flight, cancel, force, progress, failed-state all correct; 405/MCP-count unchanged; CLI completes + fast-repeat; browser button→progress→result loop works | Backend/API mechanics very strongly evidenced (see Automated Evidence + curl checks below) — every keyless-tagged piece of this journey's acceptance is covered. **The journey's own acceptance explicitly requires "browser-verified: button → progress → cells or the honest empty state"** — this was **not** performed. This is this iteration's primary deliverable, so its UI verification gap is the most consequential SKIP in this report | SKIP | none (no screenshot); strong supplementary backend evidence below |

## Skipped Tests

### UT-J-07 — The foundation is unchanged (regression sentinel)

**Verdict:** SKIPPED
**Reason:** Automated portion strongly evidenced (full suite 1489/1489 green, `test_profile_equivalence.py` 15/15, `config_fingerprint` independently confirmed = `4d665603569b9dbf` via direct Python import). **The browser portion was not verified this run** (Chrome MCP unavailable) — I could neither confirm nor refute the golden-replay lane's flagged "possible regression." See Notable Finding #3: a pre-existing screenshot in the evidence directory strongly suggests that flag was caused by the *standard* backend (port 8301) being unreachable at replay time (an infrastructure/service-availability issue), not an actual product regression — but this is circumstantial, not a re-confirmation

### UT-01 — Not-computed panel loads (cold)

**Verdict:** SKIPPED
**Reason:** Not executed — Chrome MCP unavailable. Supplementary: `curl http://localhost:8391/research/edge-report` on a freshly-seeded scoped backend (`datasets_j03`, cold cache) returned exactly `{"status":"not_computed","detail":"The 3-way strategy-comparison sweep has not been run for the current dataset registry and configuration. It never runs automatically on a GET -- an operator must trigger the compute.","dataset_count":1,"register":"simulated — assumed fees/slippage — not indicative of live results","compute":null}` — the backend payload driving this panel is confirmed correct, but the rendered button/DOM was never visually verified

### UT-02 — Full compute lifecycle

**Verdict:** SKIPPED
**Reason:** Not executed — Chrome MCP unavailable. Supplementary: triggered the same lifecycle via `curl -X POST .../research/edge-report/compute` on the scoped backend; got `state:"running"` then (near-instantly, as the test plan itself predicts for `datasets_j03`) `state:"done"`; final `GET /research/edge-report` returned `{"train":{"cells":[]},"holdout":{"cells":[]},"surviving_train_cells":[]}` — the honest empty-cells outcome (b) the test plan calls a valid pass. Backend mechanics confirmed; the actual button/progress-line/panel-swap UI was never seen

### UT-03 — Button blocks second trigger

**Verdict:** SKIPPED
**Reason:** Not executed — Chrome MCP unavailable. A manual curl-based double-POST was attempted but was inconclusive by design: the fixture resolves in ~1ms, so both sequential requests landed after the first had already reached a terminal state (each got a *different* job id, which is correct behavior for two genuinely sequential triggers, not evidence of a single-flight defect). The authoritative check is `tests/test_edge_report_compute.py::test_second_trigger_while_running_returns_the_same_job_started_false` (TC-2), which uses `threading.Event` pairs to deterministically hold a fake compute mid-flight rather than relying on wall-clock timing — this test passed as part of the full suite (see Automated Evidence)

### UT-04 — Progress line format

**Verdict:** SKIPPED
**Reason:** Not executed — Chrome MCP unavailable

### UT-05 — Failed compute shows exact error

**Verdict:** SKIPPED
**Reason:** Not executed — Chrome MCP unavailable. Supplementary: reproduced the corrupted-fixture scenario via curl (see Notable Finding #1 below) and confirmed the **exact** error string a real click would surface: `"1 dataset file(s) failed integrity verification (['5232fa672b7b4077a5117d34b14c807d.json']) — the report stops with nothing written"`. **Important:** this investigation also surfaced a likely defect in the test plan's own sub-recipe ordering — see Notable Finding #1

### UT-06 — Unreachable backend at click

**Verdict:** SKIPPED
**Reason:** Not executed — Chrome MCP unavailable. This test is **pure client-side fetch error-handling** (confirmed by reading `apps/frontend/lib/api.ts`'s `triggerEdgeReportCompute`, which catches a network failure and returns `error: "Backend unreachable — is the API running?"`); curl cannot exercise this path at all, so there is no meaningful non-browser substitute for this one

### UT-07 — Reload mid-job resumes state

**Verdict:** SKIPPED
**Reason:** Not executed — Chrome MCP unavailable

### UT-08 — Reload after failure resumes state

**Verdict:** SKIPPED
**Reason:** Not executed — Chrome MCP unavailable. Also depends on UT-05's sub-recipe, which this run's investigation found is likely mis-ordered (Notable Finding #1)

### UT-09 — J-01 not-computed render frozen

**Verdict:** SKIPPED
**Reason:** Not executed for the rendered DOM — Chrome MCP unavailable. Supplementary: curl-confirmed the backend payload text is byte-exact to the test's expected strings (see UT-01's curl evidence, same payload)

### UT-10 — Other sections unaffected (J-07)

**Verdict:** SKIPPED
**Reason:** Not executed for a real rendered view — Chrome MCP unavailable. Supplementary: fetched the raw SSR HTML via curl (`curl http://localhost:3391/structure`) and confirmed all 6 expected headings are textually present in the static shell: Tradable Map, Case Studies, Edge Report, Fetch from Yahoo Finance, Registry, Comparison. **Caveat:** the Edge Report section's dynamic content is client-fetched after hydration (confirmed it renders only the `edge-report-loading` skeleton in the raw curl HTML), so this SSR check can only prove the static shell/headings exist — it cannot prove per-section runtime behavior or absence of a client-side crash

### UT-11 — Retry succeeds after fix

**Verdict:** SKIPPED
**Reason:** Not executed — Chrome MCP unavailable. Also see Notable Finding #2: the test plan's own restore step restarts the backend, and this iteration's job state is explicitly documented as process-scoped/lost-on-restart (`docs/goal.md` Product Shape: "Job state is process-scoped bookkeeping (honestly lost on restart...)"), which appears to contradict the test plan's step-1 prediction that "Retry compute" + the old error survive that restart — flagged for the test plan's own maintainers, not a product defect

### UT-12 — Feature discoverability

**Verdict:** SKIPPED
**Reason:** Not executed — Chrome MCP unavailable

### UT-J-01 — Stop the bleeding — GET never computes

**Verdict:** SKIPPED
**Reason:** Backend/API portion strongly evidenced: curl-confirmed exact not-computed payload shape on a cold scoped instance (see UT-01); full pytest suite includes the `edge_report`/`edge_report_api`/`edge_report_cache` family (118 tests total, 0 failures) which covers the compute-spy and determinism assertions. Browser-rendered confirmation ("the warm scoped-fixture cache still renders 'No edge-report cells yet.' verbatim in the browser") was **not** performed — Chrome MCP unavailable

### UT-J-04 — The operator-run compute — button, background job, CLI warmer

**Verdict:** SKIPPED
**Reason:** Backend/API mechanics very strongly evidenced (see Automated Evidence + curl checks below) — every keyless-tagged piece of this journey's acceptance is covered. **The journey's own acceptance explicitly requires "browser-verified: button → progress → cells or the honest empty state"** — this was **not** performed. This is this iteration's primary deliverable, so its UI verification gap is the most consequential SKIP in this report

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-17

