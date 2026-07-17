# Phase goal-fast_wall-iter-1 — UI Test Results

**Phase:** goal-fast_wall-iter-1
**Date:** 2026-07-17
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 6/6 executed tests passed (0 failed). UT-07 was not executed — per this dispatch's
goal-mode regression-lane instructions, J-07 was already re-verified this iteration via
deterministic golden replay (`runs/goal-session-fast_wall/journey-scripts/J-07.json`); its row
merges into the final results automatically and is intentionally omitted here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/structure` loads, Edge Report panel visible in initial state | smoke | P1 | h1 "Structure", byline, Edge Report panel + caption present, loading placeholder visible within seconds, no crash, zero console errors | All confirmed via live DOM capture: `<h1 data-testid="structure-title">Structure</h1>`, byline text present verbatim, `[aria-label="Edge report"]` section with matching caption present, `[data-testid="edge-report-loading"]` present moments after navigation; console showed only a benign React-DevTools info line | PASS | `reports/qa/goal-fast_wall-iter-1-evidence/UT-01-initial-load.png` |
| UT-02 | Cold cache resolves to "not computed" panel within bounded time (headline) | happy-path | P1 | Amber `edge-report-not-computed` panel, headline "Edge report not computed yet.", non-empty real detail text, resolves ~30s/never >2min, `edge-report-empty` absent, no button/input inside | Resolved within the observed window (backend confirmed cold via direct GET at 29.2s just before the browser test). Rendered DOM: `<div data-testid="edge-report-not-computed">...<p>Edge report not computed yet.</p><p>The 3-way strategy-comparison sweep has not been run for the current dataset registry and configuration. It never runs automatically on a GET -- an operator must trigger the compute.</p></div>` — byte-identical to the backend's own JSON `detail`. `edge-report-empty` absent. No button/input present inside the panel (only two `<p>` tags) | PASS | `reports/qa/goal-fast_wall-iter-1-evidence/UT-02-not-computed-panel.png` |
| UT-03 | Warm cache renders frozen "No edge-report cells yet." byte-identically | regression | P1 | On a scoped, pre-warmed fixture backend: `edge-report-empty` with exact title/detail, `edge-report-register` banner, `edge-report-not-computed` absent; survives a reload | Provisioned a scoped backend (port 8391, `TAPEOLOGY_DATASET_DIR` = committed `datasets_j03` fixture) + scoped frontend (port 3391) exactly per the developer's own documented recipe, pre-warmed via `EdgeReportCache.compute_and_publish` (train/holdout cells both `[]`, matching the known fixture outcome). Rendered DOM confirmed byte-exact: register banner "simulated — assumed fees/slippage — not indicative of live results", `edge-report-empty` title "No edge-report cells yet.", detail "No recorded dataset has resolved an owning, classified scan event — an honest, valid outcome, never hidden.", `edge-report-not-computed` absent. Reloaded (F5-equivalent full navigation) — identical state re-rendered, confirming durable-cache survival | PASS | `reports/qa/goal-fast_wall-iter-1-evidence/UT-03-warm-empty-state.png` |
| UT-04 | Backend unreachable shows honest degraded panel, not a crash | error | P2 | `edge-report-unavailable` panel with exact message + reassurance line, no crash/blank page, no raw browser error page, recovers after backend returns | Chrome MCP has no network-throttle/offline-emulation action, so I substituted stopping the scoped backend I owned (port 8391, never the shared pipeline instance) and reloading the scoped frontend. Rendered DOM confirmed byte-exact: `data-testid="edge-report-unavailable"` → "Backend unreachable — is the API running?" / "Nothing cached and nothing fabricated is shown in its place." The rest of the page (h1 "Structure", Tradable Map, Case Studies) still rendered; the app additionally degrades its own top nav honestly (`data-testid="nav-unavailable"`, "navigation unavailable — backend unreachable") rather than showing dead links — no crash, no raw network-error interstitial. Restarted the scoped backend and reloaded: full recovery confirmed (`edge-report-empty` back, nav links restored to 5) | PASS | `reports/qa/goal-fast_wall-iter-1-evidence/UT-04-backend-unreachable.png` |
| UT-05 | Feature discoverable in 1 click, plain-language copy | ux | P3 | "Structure" in top nav from Cockpit, 1 click navigates to `/structure`, panel text is plain-language with no jargon, no dangling "click here" implication | Cockpit nav bar shows Cockpit/Journal/Studies/Performance/Structure; clicked "Structure" link, `window.location.href` confirmed `http://localhost:3301/structure`. Panel copy ("Edge report not computed yet." + its detail sentence, confirmed verbatim in UT-02) uses plain English, no internal terms ("cache miss", class/function names); ships no button this iteration, and the copy does not imply one exists | PASS | `reports/qa/goal-fast_wall-iter-1-evidence/UT-05-nav-to-structure.png` |
| UT-06 | Neighboring `/structure` sections unaffected | regression | P2 | Tradable Map idle message unchanged, Case Studies Symbol/Reaction filters render immediately, Fetch from Yahoo Finance panel present, no missing/duplicated/reordered sections, no console errors | Rendered DOM confirmed byte-exact: `data-testid="tradable-map-idle"` → "Choose a symbol and an as-of time, then Load, to see its tradable level map."; `data-testid="case-studies-filter-symbol"` (placeholder "e.g. AAPL") and `data-testid="case-studies-filter-reaction"` (options All/rejected/broke/chopped/…) both rendered immediately; `aria-label="Fetch from Yahoo Finance"` section present in its usual place after Edge Report. Section order unchanged (Tradable Map → Case Studies → Edge Report → Fetch from Yahoo Finance → Registry → Comparison). Console: zero errors (only benign React DevTools / Fast Refresh / HMR dev-mode log lines) | PASS | `reports/qa/goal-fast_wall-iter-1-evidence/UT-02-not-computed-panel.png` (same capture shows Tradable Map + Case Studies below the pinned Edge Report panel) |

---

## Passed Tests

### UT-01 — `/structure` loads with the Edge Report panel visible in its initial state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-1-evidence/UT-01-initial-load.png`
- Navigated fresh to `http://localhost:3301/structure`. `<h1 data-testid="structure-title">` read exactly "Structure"; byline "Load a symbol and an as-of time to see its tradable level map…" present. `<section aria-label="Edge report">` present with caption beginning "The v1 / structure_tape / structure_tape_map comparison over recorded event windows…". `[data-testid="edge-report-loading"]` confirmed present in the live DOM moments after navigation (before the fetch resolved), proving the `GET /research/edge-report` fetch auto-started on mount exactly as before this iteration. Console: only a benign React DevTools info line.

### UT-02 — Cold cache resolves to the honest "not computed" panel within a bounded time (THE headline test)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-1-evidence/UT-02-not-computed-panel.png`
- Directly confirmed via `curl` immediately before the browser test that the shared backend's edge-report cache was cold (`status: "not_computed"`, `dataset_count: 18`, 29.2s response — bounded by the still-unaccelerated `dataset_store.list()` cost, not by any sweep). Drove the real browser to `/structure`; the panel transitioned from the loading placeholder to the resolved `data-testid="edge-report-not-computed"` panel within the observed window. Live DOM capture confirmed the rendered headline "Edge report not computed yet." and detail text byte-identical to the backend's own `detail` string. `edge-report-empty` was absent at the same time. No button/input/select rendered inside the panel — this iteration ships no trigger control, matching spec.
- Note: this is the core proof that the pre-iteration always-compute hazard is gone — the page resolved promptly and the backend was not left CPU-pinned (independently corroborated by the developer's own live-verification numbers in the dev handoff: 0.5% CPU immediately after the GET).

### UT-03 — Warm cache renders the frozen "No edge-report cells yet." state byte-identically
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-1-evidence/UT-03-warm-empty-state.png`
- Provisioned a scoped backend (port 8391, `TAPEOLOGY_DATASET_DIR` pointed at the committed keyless fixture `apps/backend/tests/fixtures/datasets_j03`, isolated `TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_EDGE_REPORT_CACHE_DB` in the run's scratch dir) and a scoped frontend (port 3391, `NEXT_PUBLIC_API_URL=http://localhost:8391`) — the exact recipe the developer used and documented in `docs/handoffs/goal-fast_wall-iter-1-dev.md`'s "Live verification" section. Pre-warmed the cache directly via `EdgeReportCache.compute_and_publish(dataset_store, CONFIG, lambda: run_strategy_comparison_report(...))`, confirming `train.cells == []` and `holdout.cells == []` (the fixture's known outcome from prior `tradable_wall` iterations) and that a fresh `lookup()` served it back verbatim. Confirmed via a direct `curl` against the scoped backend's real route (8.8ms, no `status` key) before touching the browser. Then, in the browser: `edge-report-register` banner exactly "simulated — assumed fees/slippage — not indicative of live results"; `edge-report-empty` title exactly "No edge-report cells yet."; detail exactly "No recorded dataset has resolved an owning, classified scan event — an honest, valid outcome, never hidden."; `edge-report-not-computed` absent. Reloaded the page (full navigation) — identical state re-rendered from the durable SQLite row, confirming the cache survived rather than being a one-off in-process fluke.

### UT-04 — Backend unreachable shows the honest degraded panel, not a crash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-1-evidence/UT-04-backend-unreachable.png`
- Chrome MCP's `use_browser` tool exposes no offline/network-throttle action (confirmed via its own `help` output — no `set_network_conditions`/offline action exists), so DevTools "Offline" simulation as literally described in the test plan wasn't available. Substituted the equivalent real condition: stopped the SCOPED backend I had stood up for UT-03 (port 8391 — never the shared pipeline instance at 8301) and reloaded the scoped frontend against it. Live DOM confirmed `data-testid="edge-report-unavailable"` with exact text "Backend unreachable — is the API running?" and "Nothing cached and nothing fabricated is shown in its place." The rest of the page still rendered (h1 "Structure", Tradable Map, Case Studies) — no blank page. The app also degrades its top nav honestly in this state (`data-testid="nav-unavailable"`, "navigation unavailable — backend unreachable") instead of showing dead links, which is consistent with (and a nice reinforcement of) the same honesty discipline this panel embodies. No raw browser network-error interstitial appeared — the app's own fetch error-handling intercepted it. Restarted the scoped backend and reloaded: full recovery confirmed (`edge-report-empty` restored, nav back to its normal 5 links) — proving this was a transient condition, not a persisted broken state.

### UT-05 — Feature is discoverable and stated in plain language
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-1-evidence/UT-05-nav-to-structure.png`
- From `http://localhost:3301/`, the top nav shows Cockpit/Journal/Studies/Performance/Structure. Clicked "Structure"; confirmed via `window.location.href` that navigation landed on `http://localhost:3301/structure` in one click. The panel's own copy (confirmed verbatim under UT-02) — "Edge report not computed yet." plus its detail sentence — reads in plain English with no internal jargon ("cache", "sweep invocation", class/function names) and does not imply a missing control; correct for an iteration that ships no trigger yet.

### UT-06 — Neighboring `/structure` sections are unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-1-evidence/UT-02-not-computed-panel.png`
- Live DOM confirmed `data-testid="tradable-map-idle"` reading exactly "Choose a symbol and an as-of time, then Load, to see its tradable level map." Confirmed `data-testid="case-studies-filter-symbol"` (Symbol input, placeholder "e.g. AAPL") and `data-testid="case-studies-filter-reaction"` (Reaction select: All/rejected/broke/chopped/…) both render immediately, independent of how long the underlying table takes. Confirmed `aria-label="Fetch from Yahoo Finance"` section present in its usual place after Edge Report. Section order (Tradable Map → Case Studies → Edge Report → Fetch from Yahoo Finance → Registry → Comparison) unchanged from the pre-iteration structure. Console: zero errors across the whole session (only informational React DevTools / Next.js Fast Refresh / HMR dev-mode lines, never a red/error-level entry).

---

## Failed Tests

None.

---

## Skipped Tests

None SKIPPED by this agent. UT-07 (Cockpit SIM watch cross-page sentinel, mapping to Must-have journey J-07) was intentionally **not executed** — per this dispatch's goal-mode regression-lane instructions, J-07 was already deterministically re-verified this iteration via its stored golden replay script (`runs/goal-session-fast_wall/journey-scripts/J-07.json`), and its row merges into the final results automatically. This is a scoping instruction, not an environment failure.

---

## Golden Replay Script

**J-01 golden script: intentionally NOT written this iteration** (best-effort per agent instructions — "if you can't produce a clean script for a journey, skip it"). Reason, verified by reading `scripts/automation/lib/demo_runner.py` directly (`_default_timeout` and `run_verify`'s per-step `tmo` computation): the replay runner hard-clamps every step's action **and** its `expect` check to **at most 20000ms**, with no way to configure around it (`min(raw, 20000)` wraps the timeout unconditionally). The real, twice-independently-measured latency for `GET /research/edge-report` against the shared pipeline's real 882MB/18-dataset corpus is **~29 seconds** (my own `curl`: 29.2s; the dev handoff's own live verification: 28.9s) — bounded by the still-unaccelerated `dataset_store.list()` cost, which is explicitly out of this iteration's scope (J-02's future work) and not a regression. A single-step `goto /structure` + `expect: "Edge report not computed yet."` script would therefore reliably **FAIL** every future replay attempt against the same shared backend until J-02 ships store acceleration — that is not a "clean script," so none was written. `runs/goal-session-fast_wall/journey-scripts/J-01.json` does not exist; J-01 falls back to the LLM lane on the next iteration, as designed.

`J-07.json` (pre-existing) was left untouched.

---

## Environment Incident (transparency note — resolved, no lasting impact)

While provisioning UT-03/UT-04's scoped backend+frontend pair, I started a second `next dev -p 3391`
process from the **same** `apps/frontend` working directory as the shared pipeline frontend
(port 3301) without an isolated build-output directory. Both `next dev` processes concurrently
wrote to the same default `.next/` build cache, and the shared instance's `/` route was left
serving `404` (missing route manifests) for a window around 2026-07-17 ~04:52–04:58 UTC while my
own UT-01/UT-02/UT-05/UT-06 evidence (all captured *before* this happened) remained valid — those
observations were made against a healthy server. Diagnosed via `fanout-frontend-8301.log`
(`ENOENT ... app-paths-manifest.json`), fixed by killing the corrupted process tree, removing the
stale `apps/frontend/.next` (a gitignored build-cache directory — confirmed via `.gitignore:48`;
zero tracked/source files affected, confirmed via `git status`), and restarting the frontend with
the exact original environment (`NEXT_PUBLIC_API_URL=http://localhost:8301`,
`CHAIN_FRONTEND_PORT=3301`, read directly from the live process's own `/proc/<pid>/environ` before
killing it, to reproduce it exactly). Post-fix verification: `GET /`, `/structure`, `/journal`,
`/studies`, `/performance` all return `200`; a live Chrome MCP navigation to `/` renders identically
to the pre-incident screenshot with zero console errors. The backend (port 8301) was never touched
and stayed healthy throughout. Both scoped instances (8391/3391) were subsequently torn down cleanly
and both ports confirmed free.

---

## Environment

- **Frontend URL:** http://localhost:3301 (shared pipeline instance, default real-corpus backend at http://localhost:8301 — 882MB, 18 registered datasets)
- **Scoped instances used for UT-03/UT-04 only:** backend http://localhost:8391 (`TAPEOLOGY_DATASET_DIR` = `apps/backend/tests/fixtures/datasets_j03`), frontend http://localhost:3391 — both torn down after use, ports confirmed free
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (CDP)
- **Test Date:** 2026-07-17
- **Evidence directory:** `reports/qa/goal-fast_wall-iter-1-evidence/`
