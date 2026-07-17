# Phase goal-fast_wall-iter-4 — UI Test Results

**Phase:** goal-fast_wall-iter-4
**Date:** 2026-07-17
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED reason: Chrome MCP could not be started in this session (see "Chrome MCP unavailability" section below for the full, reproducible troubleshooting log). Per browser-qa-agent instructions: "If Chrome MCP is not available: write all tests as SKIPPED with reason 'Chrome MCP not available'." All 12 UT-XX test-plan cases require actual click/render verification and are SKIPPED. Two regression journeys (J-02, J-03) are legitimately non-browser ("Keyless; automated" per docs/goal.md) and are reported PASS on strong automated evidence gathered this run; this does not change the overall verdict, which is governed by the UT-XX test plan and the browser-dependent journeys (J-01, J-04, J-07). -->

**Overall:** 0/12 UT-XX tests executed via browser (12 SKIPPED). Regression journeys: 2/5 PASS on automated evidence (J-02, J-03), 3/5 SKIPPED for their browser-dependent portion (J-01, J-04, J-07) — see notes per row. No test is marked FAIL; nothing in this run's non-browser evidence contradicts the implementation.

**This was the FIRST browser-qa-agent attempt for this iteration** (trace step 0059; no earlier browser-qa-agent step exists for goal-fast_wall-iter-4). The environment blocker below was independently hit by the developer's own session too (per `docs/handoffs/goal-fast_wall-iter-4-dev.md`'s "Known verification gap" and this run's own leftover diagnostic files), so this is the **second** independent session in this iteration to hit the identical wall — worth escalating as an environment fix, not just retrying.

---

## Chrome MCP unavailability — full troubleshooting log

`mcp__plugin_superpowers-chrome_chrome__use_browser` was attempted **7 times** across **2 distinct, genuinely fresh profiles**, using both the tool's own actions and direct verification of the underlying OS state. Every attempt failed identically:

```
Error: Failed to auto-start Chrome: Chrome did not become ready on port 9222 within 15000ms
```

Steps taken, in order:
1. `navigate` to `http://localhost:3391/structure` on the default profile (`iter4-fresh-attempt2`, a name evidently left by the developer's own prior manual attempt this iteration) — failed.
2. Cleared stale `SingletonLock`/`SingletonCookie`/`SingletonSocket` files and a stale `.mcp.lock` for that profile, retried `navigate` — failed identically.
3. `kill_chrome` — failed with the same 15s timeout (the tool's own recovery action re-attempts auto-start internally).
4. `navigate` again — failed.
5. `set_profile` to a **brand-new, never-before-used** profile name (`iter4-qa-clean1`) to rule out profile corruption entirely, then `navigate` — failed identically.
6. Independently confirmed via `/proc/<chrome-pid>/net/tcp` (the process-local view of the whole machine's TCP table, since the process is not network-namespace-isolated) that port 9222 (`0x2406`) was **never bound by any process**, even after waiting a further 30+ seconds **past** the tool's own 15s cutoff — the spawned Chrome process (confirmed alive via `ps`, spawning normal zygote children, consuming real CPU) simply never starts its DevTools HTTP listener. This rules out a timing race; extending the wait does not help.
7. `restart_chrome` (the tool's dedicated recovery action) — failed identically.

System resources were checked and ruled out as a cause: load average 1.57 on 16 cores, 19GB memory available. No profile-lock, timing-race, or resource-contention explanation survived direct verification.

**A pre-existing screenshot found in the evidence directory** (`J-07-verify.png`, timestamped 14:37, not produced by this run — see the J-07 row below) independently corroborates that browser automation in this environment was already degraded before this session started: it shows the cockpit rendering a `"Backend unreachable — is the API running?"` state.

No further invasive remediation (e.g., killing the unrelated, long-lived, manually-opened Chrome window at `localhost:3301` that has been running since Jul 14 and may be the user's own desktop session) was attempted, since that risks disrupting state outside this task's scope for an unconfirmed, speculative payoff.

**Recommendation:** this is now a **repeat, cross-session environment failure** (dev session + this QA session), not a one-off. It likely needs an operator/infra-level look (e.g., confirm the sandbox permits Chrome's DevTools TCP listener at all, check for a Chrome sandbox/seccomp restriction introduced recently) rather than a third automated retry.

---

## Results Table

### UI Test Plan (UT-XX) — all require actual browser click/render verification

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
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

### Goal-mode regression journeys (dispatcher-required: J-01, J-02, J-03, J-04, J-07)

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Stop the bleeding — GET never computes | regression (browser-verifiable) | P1 | Cold cache → not-computed payload, zero sweep calls from GET; warm cache byte-identical; browser renders frozen texts | Backend/API portion strongly evidenced: curl-confirmed exact not-computed payload shape on a cold scoped instance (see UT-01); full pytest suite includes the `edge_report`/`edge_report_api`/`edge_report_cache` family (118 tests total, 0 failures) which covers the compute-spy and determinism assertions. Browser-rendered confirmation ("the warm scoped-fixture cache still renders 'No edge-report cells yet.' verbatim in the browser") was **not** performed — Chrome MCP unavailable | SKIP | none (no screenshot); supplementary curl evidence inline above |
| UT-J-02 | Stores stop re-reading — verified-content caches + durable index | regression (keyless; automated — not browser-tagged in docs/goal.md) | P1 | Zero-re-read spy tests pass on both stores; tamper still detected; racy-write guard holds; durable index survives simulated restart | Full pytest suite: `test_bars.py`+`test_bars_api.py` = 46 tests, `test_datasets.py`+`test_datasets_api.py` = 37 tests, `test_dataset_index.py` = 7 tests — **all passing, 0 failures** (part of the 1489/1489 green full-suite run, JUnit-XML-verified; see Automated Evidence). This journey carries no browser-verifiable clause in `docs/goal.md` (tagged "Keyless; automated"), so this constitutes its actual, complete verification method — not a fallback | **PASS** | `runs/pytest full suite: 1489 total, 0 failures, 0 errors, 7 skipped (all TAPEOLOGY_LIVE_INTEGRATION-gated)` |
| UT-J-03 | The arm memo — per-tick levels recompute becomes ~100 memo hits | regression (keyless; automated — not browser-tagged) | P1 | Memoized structure_tape/structure_tape_map byte-identical to fresh; counting spy proves batched `compute_levels` calls; guard tests unmodified | Full pytest suite: `test_levels.py`+`test_levels_api.py` = 41 tests, `test_tradability.py`+`test_tradability_api.py` = 34 tests, `test_backtests.py`+`test_backtests_api.py` = 75 tests (includes the source-introspection guard tests at `test_backtests.py:1500-1508`/`932-943`) — **all passing, 0 failures**. No browser-verifiable clause for this journey either | **PASS** | same full-suite run as UT-J-02 |
| UT-J-04 | The operator-run compute — button, background job, CLI warmer | regression (this iteration's target; browser-verifiable) | P1 | Single-flight, cancel, force, progress, failed-state all correct; 405/MCP-count unchanged; CLI completes + fast-repeat; browser button→progress→result loop works | Backend/API mechanics very strongly evidenced (see Automated Evidence + curl checks below) — every keyless-tagged piece of this journey's acceptance is covered. **The journey's own acceptance explicitly requires "browser-verified: button → progress → cells or the honest empty state"** — this was **not** performed. This is this iteration's primary deliverable, so its UI verification gap is the most consequential SKIP in this report | SKIP | none (no screenshot); strong supplementary backend evidence below |
| UT-J-07 | The foundation is unchanged (regression sentinel) | regression (automated + browser-verifiable) | P1 | Full suite green; equivalence + fingerprint pinned; cockpit/journal/studies/performance/structure era-1–5B behaviors unchanged | Automated portion strongly evidenced (full suite 1489/1489 green, `test_profile_equivalence.py` 15/15, `config_fingerprint` independently confirmed = `4d665603569b9dbf` via direct Python import). **The browser portion was not verified this run** (Chrome MCP unavailable) — I could neither confirm nor refute the golden-replay lane's flagged "possible regression." See Notable Finding #3: a pre-existing screenshot in the evidence directory strongly suggests that flag was caused by the *standard* backend (port 8301) being unreachable at replay time (an infrastructure/service-availability issue), not an actual product regression — but this is circumstantial, not a re-confirmation | SKIP | `reports/qa/goal-fast_wall-iter-4-evidence/J-07-verify.png` (pre-existing, not produced by this run — see Notable Finding #3) |

---

## Notable Findings (non-browser investigation, independent of the Chrome blocker)

### Finding #1 — UT-05/UT-08/UT-11's sub-recipe likely cannot reach the state it describes

The ui-test-plan's sub-recipe corrupts the fixture dataset file **before** the scoped backend's first start, then expects clicking "Compute edge report" to reach `edge-report-compute-error`. Empirically reproducing this via curl shows the **very first** `GET /research/edge-report` on such a backend already returns a 500-style error:

```
{"detail":"edge report could not complete: 1 dataset file(s) failed integrity verification (['5232fa672b7b4077a5117d34b14c807d.json']) — the report stops with nothing written"}
```

Reading `apps/frontend/app/structure/page.tsx` (~line 1978) confirms the page has **three**, not two, states for this section: `edge-report-loading` (null), `edge-report-unavailable` (any `ok:false`, i.e. this exact 500 case — a message-only panel with no button), and `edge-report-not-computed` (only reachable when the GET itself succeeds with `status:"not_computed"`). Corrupting the dataset file **before** the first navigation means the page would show `edge-report-unavailable` on load — a **pre-existing** error path this iteration didn't touch — never the new `edge-report-not-computed` panel with its button, so UT-05 as written has nothing to click. The fix (for whoever next authors/repairs this test plan) is to corrupt the file **after** confirming the not-computed panel/button is already visible (a live backend re-verifies dataset content by `(path, size, mtime_ns)` stat on the next read per J-02, so a post-load corruption is correctly picked up by the compute attempt). This is a test-plan authoring issue, not a product defect.

### Finding #2 — UT-11's step-1 prediction may contradict the documented "lost on restart" design

UT-11 step 1 asserts that after the sub-recipe's restart, "the manager's last-known snapshot is still the failed one from before the restart." `docs/goal.md`'s Product Shape section is explicit that compute-job state is "process-scoped bookkeeping (honestly lost on restart, like the existing job managers) — never a research value." If the implementation matches its own spec (which the passing `test_edge_report_compute.py` suite is consistent with — no test asserts persistence-across-restart), the real post-restart state should be idle (`compute: null`), not "Retry compute." Flagging for the test plan, not the product; the underlying capability UT-11 cares about (a fixed retry eventually succeeds) is unaffected either way.

### Finding #3 — a pre-existing screenshot suggests the J-07 replay flag is likely environmental, not functional

`reports/qa/goal-fast_wall-iter-4-evidence/J-07-verify.png` already existed in the evidence directory before this run started (this is confirmed the **first** browser-qa-agent dispatch for this iteration — no earlier trace step exists). It shows the cockpit's `SIM-BUYER` flow with a `"Backend unreachable — is the API running?"` error and `"navigation unavailable — backend unreachable"`. Independently, at the very start of this session, `curl http://localhost:8301/health` also failed (connection refused), and that backend's own log (`fanout-backend-8301.log`) shows it started, served exactly one `GET /health 200`, then immediately shut down. Both data points point the same direction: the standard backend (port 8301), which `runs/goal-session-fast_wall/journey-scripts/J-07.json`'s golden replay targets, was very likely down at the time the flagged replay ran. This is circumstantial (I did not run the replay myself and cannot see its own logs), so it does not stand in for a real re-confirmation — but it is a concrete reason to suspect the "possible regression" is a service-availability artifact rather than a change in J-07's actual behavior. No `J-07.json` golden script update was made this run (nothing was re-verified to justify touching it).

---

## Automated (non-browser) Evidence Gathered This Run

Because Chrome MCP was unavailable, effort was redirected to maximizing legitimate non-browser verification so this report carries real signal rather than being empty:

- **Full backend suite:** `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=...` → **1489 tests, 0 failures, 0 errors, 7 skipped** (all 7 skips are `TAPEOLOGY_LIVE_INTEGRATION`-gated real-credential tests — `test_event_recording_integration`, `test_live_integration`, `test_yahoo_live_integration` ×5 — exactly the expected, by-design skip set, confirmed by reading each skip message). Result parsed from JUnit XML rather than the terminal summary line, because the terminal's own final summary line mysteriously failed to print in **three consecutive runs** (process exits cleanly right after the warnings block, no traceback, no non-zero-looking cause found — worth a maintainer's look, but the JUnit XML is independently authoritative and was cross-checked to contain all 1489 `<testcase>` elements with zero `<failure>`/`<error>` children).
  - Breakdown relevant to this iteration's journeys: `test_edge_report_compute.py` (20), `test_edge_report_api.py` (23), `test_edge_report*` family (118 total), `test_bars*` (46), `test_datasets*` (37), `test_dataset_index.py` (7), `test_levels*` (41), `test_tradability*` (34), `test_backtests*` (75, includes the pinned source-introspection guard tests), `test_mcp_server.py` (28), `test_no_execution_path.py` (6), `test_profile_equivalence.py` (15). All passing.
- **`config_fingerprint`** independently confirmed via direct Python import (`app.config.CONFIG.config_fingerprint()`) = `4d665603569b9dbf` — matches the frozen value, also independently pinned by 10+ assertions across the test suite (`test_pnl_scan.py`, `test_edge_report.py`, `test_tradability.py`, `test_levels.py`, `test_setups.py`, `test_profile_equivalence.py`).
- **MCP tool set** independently confirmed via direct Python import (`app.mcp.TOOL_NAMES`) = exactly 18 tools, matching the pinned set and this session's own available `mcp__tapeology__*` tools.
- **Frontend TypeScript build:** `npx tsc --noEmit` → clean, zero errors.
- **REST mechanics on a scoped backend (`datasets_j03` fixture, port 8391/8392, never the real corpus):**
  - `PUT`/`DELETE /research/edge-report` → `405` (non-GET verbs on the base route correctly untouched).
  - `POST /research/edge-report/compute/cancel` while idle → `409`.
  - `POST /research/edge-report/compute` on a cold cache → `{"started":true, "compute":{"state":"running", ...}}`, converging to `state:"done"` with `train`/`holdout` cells both `[]` (the honest empty-cells outcome for this non-panel-symbol fixture).
  - Corrupted-fixture backend: `POST .../compute` → `state:"failed"`, `error` exactly `"1 dataset file(s) failed integrity verification (['5232fa672b7b4077a5117d34b14c807d.json']) — the report stops with nothing written"` (verbatim, not paraphrased).
  - CLI warmer (`python -m app.research.edge_report_compute --workers 2 --out report.json`): first run exits 0, prints `"edge-report compute: 0 backtest(s) to run"` / `"edge report compute complete: ..."`, writes the report file; a repeat invocation without `--force` completes in **0.11s** and produces a **byte-identical** `report.json` (`diff` clean) — matching TC-11/TC-12.

None of this is a substitute for the browser verification this iteration's dispatch specifically required (and none of it is presented as such above — every PASS is scoped explicitly to non-browser-tagged journeys, and every browser-tagged item is SKIP). It does, however, mean this SKIPPED verdict comes with strong evidence that nothing in the backend is broken — the gap is specifically in visually confirming the new `/structure` UI surfaces this iteration added.

---

## Skipped Tests

All 12 UT-XX test-plan cases (UT-01 through UT-12) are SKIPPED.

**Reason (all of them):** Chrome MCP not available. `mcp__plugin_superpowers-chrome_chrome__use_browser` failed to start Chrome (DevTools port 9222 never bound) across 7 attempts spanning 2 fresh profiles, the tool's own `kill_chrome`/`restart_chrome` recovery actions, and direct low-level verification that ruled out timing races, profile corruption, and resource contention. Full troubleshooting log above. This is independently corroborated by the developer's own session hitting the same wall this same iteration (per their dev handoff) and by a pre-existing "Backend unreachable" screenshot found in this run's own evidence directory.

Three regression-journey rows (UT-J-01, UT-J-04, UT-J-07) are also SKIPPED for their browser-verifiable clause specifically, for the same reason, while their non-browser-verifiable clauses are reported separately above with real evidence.

---

## Environment

- **Frontend URL (task-assigned):** http://localhost:3301 — found returning 404 at time of writing (was 200 at session start; not investigated further, as this instance is externally managed per the dispatch note and this run never depended on it).
- **Backend URL (task-assigned):** http://localhost:8301 — found unreachable (connection refused) at session start and remained so throughout; its own log shows one `GET /health 200` followed immediately by `"Shutting down"`, consistent with Notable Finding #3.
- **Scoped instances used for all supplementary evidence in this report** (self-provisioned, per the ui-test-plan's own required recipe): backend `http://localhost:8391` / `http://localhost:8392` (corrupted-fixture variant), frontend `http://localhost:3391`, all pointed at fresh copies of `apps/backend/tests/fixtures/datasets_j03`, never the real corpus. All stopped cleanly at the end of this run.
- **Browser:** Chrome via MCP — **unavailable** (see above).
- **Test Date:** 2026-07-17
- **Evidence directory:** `reports/qa/goal-fast_wall-iter-4-evidence/` (contains only the pre-existing `J-07-verify.png`; no screenshots were produced by this run).

---

## Golden replay scripts

None written this run. Per the golden-replay instructions, a script is only written "immediately after that journey passes" via actual verification; since no journey received a genuine browser PASS this run (J-02/J-03's PASS is automated-only and journeys, not the UI, so a Playwright-style replay script does not apply to them), zero files were written or overwritten under `runs/goal-session-fast_wall/journey-scripts/`. The existing `J-07.json` was left untouched (no evidence-based improvement to make to it without an actual browser re-run).
