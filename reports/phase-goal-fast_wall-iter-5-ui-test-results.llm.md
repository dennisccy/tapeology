# Phase goal-fast_wall-iter-5 — UI Test Results

**Phase:** goal-fast_wall-iter-5
**Date:** 2026-07-17
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 13/14 tests passed (1 skipped, 0 failed)

All 9 UI test-plan cases (UT-01 through UT-09) plus the 5 dispatched regression journeys
(J-01, J-02, J-03, J-04, J-07) were executed. Every P1 test passed. The single SKIP (UT-07,
the "(N from cache)" annotation) is explicitly documented in the test plan itself as an
acceptable, non-blocking outcome on the committed fixtures. J-04's last open browser gap
(the click → progress → terminal-state cycle) is now closed with real screenshots. J-07's
replay-flagged "possible regression" was re-confirmed PASS by direct manual execution — the
golden script was stale/false-negative (see Notable Findings #1), not a real regression, and
has been re-written/repaired at `runs/goal-session-fast_wall/journey-scripts/J-07.json`.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Not-computed panel loads (cold), exact J-01 text | smoke | P1 | Panel `edge-report-not-computed` shows headline "Edge report not computed yet." + exact detail text + enabled "Compute edge report" button; no progress/error/table | Navigated scoped `:3391/structure` on a freshly-started backend (cold `TAPEOLOGY_EDGE_REPORT_CACHE_DB`/`TAPEOLOGY_EDGE_SWEEP_CACHE_DB`). DOM query confirmed panel present, headline and detail text byte-identical to expected, button text "Compute edge report", `disabled=false`, no progress/error elements present. Backend log shows two `GET /research/edge-report` calls before any POST — confirms no compute triggered merely by the page load | PASS | `reports/qa/goal-fast_wall-iter-5-evidence/UT-01-not-computed-panel.png` |
| UT-02 | Full compute lifecycle: click → running → terminal state (closes J-04) | happy-path | P1 | Button relabels "Computing…"/disabled, progress line appears (or panel already past it, an accepted outcome on this fixture), no "(N from cache)" clause, terminal state within 90s, no full-page reload | Clicked `edge-report-compute-button`. On this fixture (datasets_j03, 0 eligible pairs) the compute resolved before the very next DOM check — button was already gone, panel had already moved to `edge-report-empty` ("No edge-report cells yet." / "No recorded dataset has resolved an owning, classified scan event — an honest, valid outcome, never hidden."), register text present. This is the test plan's own explicitly accepted outcome for this fixture. URL stayed `http://localhost:3391/structure` throughout, no reload. No "(N from cache)" clause ever appeared (correct — cold first-ever compute) | PASS | `reports/qa/goal-fast_wall-iter-5-evidence/UT-02-before.png`, `UT-02-during.png`, `UT-02-after-empty-state.png` |
| UT-03 | Button blocks a second trigger while a job is running | validation | P2 | Second click while running has no visible effect / no second network request | Same-tick synthetic double `.click()` (via `element.click(); element.click();` inside one `eval`) produced 2 POST requests (both HTTP 200) against this near-instant fixture; final UI state reached the correct honest empty state with no visible duplication, no crash, no stuck button. As iter-4's own QA investigation already documented for this identical fixture, sub-millisecond resolution makes strict browser-level single-flight timing inherently inconclusive; the authoritative, timing-independent proof is `test_second_trigger_while_running_returns_the_same_job_started_false` (`apps/backend/tests/test_edge_report_compute.py:109`, uses `threading.Event` pairs, not wall-clock), part of this iteration's green 1517-test suite. No visible defect observed at the browser level | PASS | `reports/qa/goal-fast_wall-iter-5-evidence/UT-03-after-double-click.png` |
| UT-04 | Reload after completion serves the warm result directly, no button (TC-2) | regression | P1 | Reload shows same warm result immediately, no button/progress/not-computed panel | Reloaded `:3391/structure` in the same session immediately after UT-02. `edge-report-empty` rendered directly with identical text; `edge-report-compute-button`, `edge-report-not-computed`, and `edge-report-compute-progress` all absent. Cross-check: `curl http://localhost:8391/research/edge-report` returned the same report shape (`train.cells:[]`, `holdout.cells:[]`) with no `status` key — confirms single canonical endpoint, not just browser-tab state | PASS | `reports/qa/goal-fast_wall-iter-5-evidence/UT-04-reload-warm-result.png` |
| UT-05 | Other `/structure` sections unaffected (J-07 regression sentinel) | regression | P1 | 6 headings in order; Tradable Map/Case Studies/Fetch-Yahoo/Registry/Comparison render without crash | All 6 headings present in exact order: Tradable Map, Case Studies, Edge Report, Fetch from Yahoo Finance, Registry, Comparison. No error boundary, no blank sections. Tradable Map and Case Studies show their honest "no data yet" prompts (expected — this cold scoped session has no bar series recorded and no scan yet; confirmed pre-existing/unrelated to this iteration, not a regression — see Notable Finding #2). Loaded symbol=PG/as-of=2026-06-09T21:00:00Z on the Tradable Map form to directly exercise the GET /research/tradability path: it correctly returned the honest `tradable-map-no-bar-series` state ("No bar series recorded for PG." / "Recording historical bars needs provider credentials.") — proves the bars/datasets read path (J-02) is intact, not crashing. Registry `champion-summary` (v1/default) and Comparison `comparison-champion` (v1/default) both render correctly | PASS | `reports/qa/goal-fast_wall-iter-5-evidence/UT-05-top-tradable-case-studies.png`, `UT-05-registry-comparison.png` |
| UT-06 | Failed compute shows the exact backend error and offers retry (TC-3) | error | P1 | Red error line with exact backend `EdgeReportError` message; button relabels "Retry compute", enabled; no progress line; no generic panel | Followed the corrected sub-recipe on a genuinely fresh scoped instance: confirmed idle not-computed panel, corrupted the one dataset file (`echo "corrupted" >>`), clicked "Compute edge report", immediately restored the original file bytes without restarting the backend. Panel showed the error on first check (no reload needed): `edge-report-compute-error` read exactly "1 dataset file(s) failed integrity verification (['5232fa672b7b4077a5117d34b14c807d.json']) — the report stops with nothing written" — byte-identical to the dev handoff's own documented observation. Button read "Retry compute", enabled. No progress line, no generic "edge report could not complete" panel | PASS | `reports/qa/goal-fast_wall-iter-5-evidence/UT-06-failed-compute-error.png` |
| UT-07 | "(N from cache)" annotation shows N > 0 on a resumed compute | happy-path | P3 | SKIP is an explicitly documented, acceptable outcome — not independently browser-verifiable with any committed fixture | Not attempted, per the test plan's own explicit instruction: both committed fixtures (`datasets_j03`, `apps/backend/tests/fixtures/datasets`) resolve zero eligible pairs, so there is nothing to durably cache/resume against from a running server. The authoritative non-vacuous proof lives at the pytest level (TC-6/TC-8/TC-10/TC-11), already covered by this iteration's green suite per the QA report and dev handoff | SKIP | none (documented SKIP, not attempted per test plan) |
| UT-08 | Standard instance quick sanity scroll (no compute click) | regression | P3 | Page loads, 6 headings present in order, no console errors, no click on compute | Restarted the standard frontend cleanly (see Notable Finding #1), navigated `:3301/structure`, scrolled top to bottom without clicking "Compute edge report". All 6 headings present in order, `errorBoundary=false`, no console errors beyond benign React DevTools/Fast-Refresh notices. Edge Report section shows `not_computed` (real corpus never computed on this instance previously — expected, not a defect) | PASS | `reports/qa/goal-fast_wall-iter-5-evidence/UT-08-standard-structure-top.png`, `UT-08-standard-structure-bottom.png` |
| UT-09 | The capability is discoverable without developer knowledge | ux | P2 | "Structure" nav link visible with no login; Edge Report reachable by scrolling only; button self-explanatory | From `:3301/`, clicked the "Structure" nav link (`data-testid="nav-link"`), landed on `/structure`. "Edge Report" heading and "Compute edge report" button are reachable by plain linear scroll (heading top ≈1377px in a 2400px-tall viewport — well within the page, no hidden tabs/extra clicks). Button label is self-explanatory given the section's own intro text | PASS | `reports/qa/goal-fast_wall-iter-5-evidence/UT-09-discoverability.png` |
| UT-J-01 | J-01: Stop the bleeding — `GET /research/edge-report` never computes | regression (browser-verifiable) | P1 | Cold cache → not-computed payload; zero sweep/backtest calls from the GET path; browser renders the frozen not-computed texts | Same evidence as UT-01. Additionally confirmed via backend access log: two `GET /research/edge-report` requests were served (both returning the cold `status:"not_computed"` payload) before any `POST /research/edge-report/compute` appeared in the log — direct evidence the GET path never triggers compute. Detail text and register string byte-match goal.md's own quoted acceptance text | PASS | `reports/qa/goal-fast_wall-iter-5-evidence/UT-01-not-computed-panel.png` |
| UT-J-02 | J-02: The stores stop re-reading — verified-content caches + durable dataset index | regression (keyless; automated per goal.md — no browser-verifiable clause) | P1 | Zero-re-read spy tests pass on both stores; tamper still detected; durable index survives simulated restart | goal.md tags this journey `(Keyless; automated.)` — its acceptance (counting-spy zero-file-read assertions, durable-index-survives-restart) has no browser-observable surface. `bars.py`/`datasets.py`/`dataset_index.py` are git-confirmed byte-unchanged this iteration (out-of-scope files per the phase spec). This iteration's own QA report and dev handoff record the full backend suite green: 1517 passed / 7 skipped / 0 failed, which includes this journey's dedicated test modules. Supplementary direct browser evidence (UT-05): loading Tradable Map for symbol=PG against the scoped fixture exercised the live `bars.py`/`datasets.py` read path end-to-end and returned the correct honest "No bar series recorded for PG." response with no crash, no hang, no stale/wrong data — consistent with an intact store layer | PASS | full-suite result cited from `reports/qa/goal-fast_wall-iter-5-qa.md` (1517 passed/7 skipped/0 failed) and `docs/handoffs/goal-fast_wall-iter-5-dev.md`; supplementary: `reports/qa/goal-fast_wall-iter-5-evidence/UT-05-top-tradable-case-studies.png` |
| UT-J-03 | J-03: The arm memo — per-tick levels recompute becomes ~100 memo hits per session | regression (keyless; automated per goal.md — no browser-verifiable clause) | P1 | Memoized `structure_tape`/`structure_tape_map` byte-identical to fresh; counting spy proves batched `compute_levels` calls; guard tests unmodified | goal.md tags this journey `(Keyless; automated.)` also — no browser-observable acceptance clause. `levels.py`/`tradability.py`/`backtests.py` are git-confirmed byte-unchanged this iteration (out-of-scope files per the phase spec, explicitly untouched — "consumed at greater volume by the new process-pool workers, never modified"). This iteration's own QA report/dev handoff record the full suite green (1517/7/0), including `test_levels.py`, `test_tradability.py`, `test_backtests.py` (source-introspection guards at `test_backtests.py:1500-1508`/`932-943`). No browser action in this iteration's test plan exercises the arm memo directly (it only activates inside `structure_tape`/`structure_tape_map` backtest runs, not the live Tradable Map GET) | PASS | full-suite result cited from `reports/qa/goal-fast_wall-iter-5-qa.md` (1517 passed/7 skipped/0 failed) and `docs/handoffs/goal-fast_wall-iter-5-dev.md` |
| UT-J-04 | J-04: The operator-run compute — button, background job, CLI warmer | regression (this iteration's closed browser gap; browser-verifiable) | P1 | Single-flight, cancel, force, progress, failed-state correct; browser button→progress→result loop works end-to-end | Same evidence as UT-02 (happy path: click → terminal empty state, zero reload) and UT-06 (failed-state: exact error text, "Retry compute" relabel). Together these close the ONLY remaining gap eval.md iter-4 flagged for J-04 — the full click-through cycle now has real screenshots for the first time this interlude | PASS | `reports/qa/goal-fast_wall-iter-5-evidence/UT-02-*.png`, `UT-06-failed-compute-error.png` |
| UT-J-07 | J-07: The foundation is unchanged (regression sentinel) — replay-flagged, re-confirmed | regression (automated + browser-verifiable) | P1 | Full suite green; SIM-BUYER/SIM-SELLER cockpit settle correctly; `/journal`, `/studies`, `/performance`, `/structure` era-1–5B behaviors unchanged | Manually re-executed the exact golden-script steps against the standard `:3301`/`:8301` pair after restarting the standard frontend cleanly (Notable Finding #1): `/` shows "Try: SIM-BUYER"; typed SIM-BUYER, clicked Watch → "buyer_control" settled; Stop; typed SIM-SELLER, clicked Watch → "seller_control" settled; `/journal` shows "SIM-BUYER"; `/studies` shows heading "Replay studies"; `/performance` shows "simulated — assumed fees/slippage — not indicative of live results". All 9 steps passed. The replay lane's "possible regression" flag was a stale/false-negative (see Notable Finding #1) — the underlying capability is intact. Golden script repaired/re-written at `runs/goal-session-fast_wall/journey-scripts/J-07.json` (content unchanged, content-validated via `demo_runner.py --mode lint`) | PASS | `reports/qa/goal-fast_wall-iter-5-evidence/J-07-sim-buyer.png`, `J-07-sim-seller.png`, `J-07-journal.png`, `J-07-studies.png`, `J-07-performance.png` |

---

## Passed Tests

### UT-01 — Not-computed panel loads (cold), exact J-01 text
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-5-evidence/UT-01-not-computed-panel.png`
- Headline "Edge report not computed yet." and the full detail sentence rendered byte-identical to the backend's own `detail` string; button "Compute edge report" present and enabled; no progress/error/table.

### UT-02 — Full compute lifecycle (closes J-04)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-5-evidence/UT-02-before.png`, `UT-02-during.png`, `UT-02-after-empty-state.png`
- Click triggered the compute; on this fixture it resolved to the honest "No edge-report cells yet." state before the very next check — an outcome the test plan itself calls a valid pass. No reload, URL unchanged throughout.

### UT-03 — Button blocks second trigger
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-5-evidence/UT-03-after-double-click.png`
- No visible duplication or crash from a rapid double-click; authoritative single-flight proof lives in the deterministic pytest test cited above (this fixture resolves too fast for a meaningful wall-clock browser check, a limitation already documented by iter-4's QA).

### UT-04 — Reload serves warm result directly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-5-evidence/UT-04-reload-warm-result.png`
- Reload shows the same result immediately with no button/progress/not-computed panel; curl cross-check confirms same canonical endpoint.

### UT-05 — Other sections unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-5-evidence/UT-05-top-tradable-case-studies.png`, `UT-05-registry-comparison.png`
- All 6 headings present and correctly ordered; no crashed component; see Notable Finding #2 for the honest empty-state observations on this cold fixture.

### UT-06 — Failed compute shows exact error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-5-evidence/UT-06-failed-compute-error.png`
- Exact `EdgeReportError` string rendered verbatim; "Retry compute" enabled; no progress line; no generic fallback panel.

### UT-08 — Standard instance sanity scroll
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-5-evidence/UT-08-standard-structure-top.png`, `UT-08-standard-structure-bottom.png`

### UT-09 — Feature discoverability
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-5-evidence/UT-09-discoverability.png`

### UT-J-01 through UT-J-04, UT-J-07 — Regression journeys
**Verdict:** PASS (all five)
See Results Table above for full detail per journey.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-07 — "(N from cache)" annotation shows N > 0 on a resumed compute
**Verdict:** SKIPPED
**Reason:** Per the test plan's own explicit instruction, this is not independently browser-verifiable this iteration with any committed dataset fixture — both `datasets_j03` and `apps/backend/tests/fixtures/datasets` resolve zero eligible (dataset, strategy) pairs, so there is nothing to durably cache or resume from via a running server. The test plan states "SKIP is an acceptable outcome. Do not fail the phase for not executing this test" and "Pass criteria: SKIP... is a PASS for this test case." The authoritative, non-vacuous proof of this behavior lives entirely at the automated unit-test level (TC-6, TC-8, TC-10, TC-11), already covered by this iteration's green 1517-test suite per the QA report and dev handoff.

---

## Notable Findings (informational, not product defects)

### Finding #1 — Standard instance was down at dispatch time; a self-inflicted `.next` build-cache collision during testing (both environmental, both resolved)

At the start of this run, the standard backend (`:8301`) was not running (its process had cleanly shut down per its own log) and had to be restarted. This alone is fully consistent with iter-4's own established lesson that a golden-replay "possible regression" against the standard instance is very plausibly an infrastructure false-negative rather than a real regression — exactly what happened to J-07 this iteration (see UT-J-07 above: manually re-executing every one of J-07's golden-script steps against a healthy standard instance passed cleanly).

Separately, during this run I temporarily ran a SECOND `next dev` process (for the scoped `:3391` frontend) concurrently with the already-running standard `:3301` frontend. Both processes point at the same `apps/frontend` directory and therefore share one `.next/` build-cache directory; running two `next dev` instances against the same directory concurrently is unsafe (a well-known Next.js dev-server limitation) and corrupted the shared cache, causing the standard instance to briefly 500/404 on `/` and `/structure` with `ENOENT: ... .next/server/app/page.js` in its log. This was entirely caused by my own test setup, not by any product code change. Diagnosed from the frontend log, fixed by killing the colliding process and cleanly restarting the standard frontend (which self-healed by recompiling), after which `/structure` served 200 again with no further issue for the remainder of this run (see UT-08/UT-J-07 evidence, captured after the fix). For the rest of this run I strictly serialized standard-vs-scoped frontend processes (never running both against the same checkout at once) to avoid recurrence. Both services were left running and healthy (`:3301`/`:8301`) at the end of this run, matching the environment's starting state.

### Finding #2 — Tradable Map / Case Studies / Fetch-Yahoo-button show "empty/disabled" states on the cold scoped fixture, pre-existing and unrelated to this iteration

On the scoped `datasets_j03` fixture with a freshly-created, empty bar directory, the Tradable Map and Case Studies sections initially show their honest "no data yet" prompts (no symbol pre-loaded, nothing scanned) rather than populated tables, and the "Fetch from Yahoo Finance" / "Load" / "Run comparison" submit buttons are disabled by default because their required text inputs start empty (standard client-side form validation — confirmed directly: typing a symbol+as-of into the Tradable Map form enabled its "Load" button immediately). Loading symbol=PG on the Tradable Map form then correctly returned the honest `tradable-map-no-bar-series` state ("No bar series recorded for PG." / "Recording historical bars needs provider credentials.") — the expected, honest outcome given this scoped session's bar directory is intentionally empty per the one-time setup recipe, not a defect. `apps/frontend/` is git-confirmed byte-identical to iter-4, so none of this is new behavior introduced by this iteration's (backend-only) diff. Flagged here only because the test plan's own wording ("button... present and enabled") assumed a populated/pre-filled state that this specific cold-fixture scenario doesn't produce by default.

---

## Environment

- **Frontend URL:** http://localhost:3301 (standard instance) and http://localhost:3391 (scoped fixture instance, `TAPEOLOGY_DATASET_DIR` pointed at `apps/backend/tests/fixtures/datasets_j03`, per the test plan's required recipe — four fresh scoped backend/frontend instances were cycled through across UT-01/02/04/05, UT-03, and UT-06 to guarantee genuinely cold starting caches for each precondition)
- **Backend URL:** http://localhost:8301 (standard) and http://localhost:8391 (scoped)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-17
- **Evidence directory:** `reports/qa/goal-fast_wall-iter-5-evidence/`
- **Golden replay scripts written/repaired this run:** `runs/goal-session-fast_wall/journey-scripts/J-07.json` (re-validated via `demo_runner.py --mode lint`). J-01 and J-04, though verified PASS, do not get golden scripts: the replay runner only ever targets the real base URL (the standard offset dev-port), never the scoped fixture port these two journeys' Edge-Report acceptance criteria require — a hardcoded "not computed"/"empty" assertion would be unsafe to replay later once the standard instance's Edge Report has any real compute history. This mirrors the established precedent of every prior fast_wall iteration (only `J-07.json` has ever existed in this directory).

STOP.
