# Goal Iteration goal-rapid-microscope-iter-1 — UI Test Results

**Phase:** goal-rapid-microscope-iter-1
**Date:** 2026-08-17
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: J-01 (this iteration's target journey, P1/happy-path) does not meet its written
     Acceptance on the mandated store-scoped QA backend — see UT-J-01 below. This is a data/
     test-infrastructure gap in a shared, pre-existing fixture rig, NOT a defect found in the
     new frontend or backend code; see the Root Cause note in the Failed Tests section. -->

**Overall:** 1/2 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | functional | P1 | `GET /research/desk/micro/readiness` serves `distinct_symbol_days: 12`, `session_equivalents` ≈ 3.0, 18 legacy shards each tagged `exploratory`/`hand_assigned`, and a floors table where all 3 pilot studies read `floor_unmet`; the `/desk` Microscope Readiness section (below Referee Runs) renders those same served values verbatim (element screenshot). | Section renders in the correct place (below Referee Runs, last section), with its own unique `data-testid`, correct structure (Corpus Totals / Legacy Tick Shards / Pilot-Study Floors / integrity errors), and **every displayed value is byte-identical to the GET response body** — zero client-side arithmetic, confirmed field-by-field. But the GET response itself, on the mandatory store-scoped QA backend, serves `distinct_symbol_days: 0`, `distinct_datasets: 0`, `shards: []` ("No tick shards recorded."), and all 3 floor rows at `available_sessions: 0` (still `floor_unmet`, but not for the reason the acceptance names). Confirmed root cause: `TAPEOLOGY_DATASET_DIR` on backend PID 1675605 points at the empty rig fixture directory (0 files); the rig's shared seeder script never populates a tick-dataset fixture; the real 18-file/12-symbol-day corpus sits untouched at the protected `apps/backend/.data/datasets/` path. | FAIL | `reports/qa/goal-rapid-microscope-iter-1-evidence/UT-J-01-fail.png` |
| UT-J-10 | The kept product stands — traps armed, sentinel green (browser-testable sentinel subset per this iteration's scope: cockpit `/`, `/structure` load + Tradable Map, every shipped `/desk` section) | regression | P1 | Cockpit live-tape + chart, `/structure` load + Tradable Map, and every shipped `/desk` section (Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs) render exactly as shipped — zero regression from the new Microscope Readiness section landing on the same `/desk` page. | All verified working, real fixture data, zero console errors on any page. Cockpit: watched `SIM-BUYER`, live tape connected (`Tape state changed to buyer_control`, Tape State "Buyer Control" confidence 0.912, Quote/Features/Recent Trades/Observations/Event Log all populated, 10s candle chart rendering, "Live" indicator green, lag 0.3s). `/structure`: loaded AAPL as-of 2026-06-22 17:00:00, Tradable Map rendered real quality-scored bands (e.g. resistance 300.11–302.2, Class A, score 171, 849 members, round-number flag), candles chart with as-of marker. `/desk`: expanded Playbook Evidence (real pooled-signature content, "Built from signature: b06e0bc289c54d77"), Referee Registry (Evidence Readiness shows `config fingerprint 08e471b10130e1e2` — matches the frozen pin), Referee Adjudications ("No hypotheses registered." honest empty state), Referee Runs ("No null-build runs recorded yet." / "No evaluation runs recorded yet.") — all render their correct content, no crashes, no `data-testid`/heading collisions with the new Microscope Readiness section. | PASS | `reports/qa/goal-rapid-microscope-iter-1-evidence/UT-J-10-cockpit.png`, `UT-J-10-structure.png`, `UT-J-10-desk-sections.png` |

---

## Passed Tests

### UT-J-10 — The kept product stands — traps armed, sentinel green
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-1-evidence/UT-J-10-cockpit.png`, `reports/qa/goal-rapid-microscope-iter-1-evidence/UT-J-10-structure.png`, `reports/qa/goal-rapid-microscope-iter-1-evidence/UT-J-10-desk-sections.png`

Scope note: this iteration's own spec (`docs/phases/goal-rapid-microscope-iter-1.md`, TESTING REQUIREMENTS) narrows J-10 to its **browser-testable sentinel subset** — cockpit `/`, `/structure` load + Tradable Map, and every shipped `/desk` section — explicitly "via the store-scoped rig." The full J-10 acceptance (TR-1…TR-22 trap suite, deterministic rerun, full backend suite, fingerprint check, referee SHA-256 listing) is backend/unit-test territory landing across J-02…J-10 and is out of browser-qa-agent's remit; not exercised here.

- **Cockpit (`/`):** typed `SIM-BUYER` into the Ticker field, clicked Watch. Live tape connected within the wait budget: Tape State panel showed "Buyer Control" at confidence 0.912, Quote panel showed real Bid/Ask/Spread/Last (101.28/101.30/0.02/101.30), Features panel populated (trade speed, aggressive buy/sell ratios, price impact, absorption/refresh scores), Recent Trades table showed 14 real rows, Observations showed 3 real bullet lines, Event Log showed "Tape state changed to buyer_control", the 10s candle chart rendered live bars, and the header showed "Live" (green) at lag 0.3s. No console errors.
- **Structure (`/structure`):** entered symbol `AAPL`, as-of `2026-06-22 17:00:00`, clicked Load. "Map basis (prior completed session close): 2026-06-18 00:00:00 ET" appeared, the daily candle chart rendered with an as-of marker, and the Tradable Map table populated with real quality-scored bands, e.g. resistance `300.11–302.2`, Class A, score 171, 849 members, flagged `round number` — matching this project's previously-established AAPL 300–302 wall example. No console errors.
- **`/desk` shipped sections:** expanded all four (Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs) via their `data-testid`s (`desk-section-expand-playbookEvidence`, `-refereeRegistry`, `-refereeAdjudications`, `-refereeRuns`). Playbook Evidence rendered its full pooled-signature disclosure copy and cohort breakdown with real values (2 records pooled from 2026-06-25/2026-08-07, signature `b06e0bc289c54d77`, 2 other signatures listed). Referee Registry's Evidence Readiness subsection served `config fingerprint 08e471b10130e1e2` for the Playbook Family — matches the era's frozen fingerprint pin — and an honest "0 tick dataset(s) are registered today, 150 short of the gate" statement for the Strategy Family (consistent with the same empty-corpus rig condition found in UT-J-01, corroborating that finding as pre-existing and cross-cutting, not new). Referee Adjudications and Referee Runs both rendered correct, honest empty-ledger copy. No crashes, no console errors, and the new Microscope Readiness section's `data-testid`/heading do not collide with any of these four.
- Golden replay script written to `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` and lint-checked clean (`demo_runner.py --mode lint`).

---

## Failed Tests

### UT-J-01 — The era transition stands — the corpus truth on the record
**Verdict:** FAIL
**Failure:** `GET /research/desk/micro/readiness` on the mandatory store-scoped QA backend (`http://localhost:8301`) serves an EMPTY corpus (`distinct_symbol_days: 0`, `distinct_datasets: 0`, `shards: []`, all 3 study-floor rows at `available_sessions: 0`) instead of the acceptance-mandated real corpus (`distinct_symbol_days: 12`, `session_equivalents` ≈ 3.0, 18 shards). The `/desk` Microscope Readiness section renders this empty response correctly and verbatim, so the ACCEPTANCE AS WRITTEN — which names concrete real-corpus values — is not observable via the browser-QA channel this run.
**Evidence:** `reports/qa/goal-rapid-microscope-iter-1-evidence/UT-J-01-fail.png` (full-page screenshot, Microscope Readiness section expanded, showing the served-but-empty totals/shards/floors)

**Steps taken:**
1. Navigated to `http://localhost:3301/desk`. Confirmed "Microscope Readiness" is the last section on the page, positioned directly below "Referee Runs" (T-11 placement requirement met).
2. Inspected the collapsed section's markup: `data-testid="desk-section-expand-microReadiness"`, unique and non-colliding with any shipped section's testid.
3. Clicked the expand control. The section fetched and rendered: Corpus Totals (Distinct symbol-days 0, Distinct datasets 0, RTH minutes covered 0.00, Session-equivalents 0.0000, Referee tick-gate 150), Legacy Tick Shards ("No tick shards recorded."), Pilot-Study Floors (3 rows: `range_wall_failed_aggression` / `delta_divergence_level_tests` / `capitulation_exhaustion`, each `wf_fold_geometry`, required 60, available 0, `floor_unmet`), and "No integrity errors."
4. Cross-checked via `curl http://localhost:8301/research/desk/micro/readiness` directly: response body matches the rendered UI values exactly, field for field — confirming the frontend correctly and verbatim displays whatever the backend serves (zero client-side computation, satisfying the Data Contract's own rule).
5. Investigated why the backend serves an empty corpus rather than the real one: read the backend process's environment (`/proc/1675605/environ`) and found `TAPEOLOGY_DATASET_DIR=<TMPDIR>/tapeology-store-scope-qa/rig/datasets`, an empty directory (`ls` confirmed 0 files) — this is the project's own store-scope QA rig (`project-extensions/store-scope/store-scope.env`, `apps/backend/scripts/start_scoped_qa_backend.sh`, `assert_scoped_qa_backend.py`), which deliberately swaps the ambient backend for a fixture-scoped one on the QA port so browser lanes can never write into the real, protected `apps/backend/.data/` stores (a hard project rail, not a bug). Confirmed via `GET /research/desk/universe` that this backend's `source_url` starts with `fixture-rig`, i.e. it IS provably the scoped rig, exactly as intended.
6. Read the rig's seeder script (`apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`): it creates the `datasets/` directory but never seeds any tick-dataset fixture into it — it was built for playbook/bars/universe QA (era B2/Referee), which never needed tick-dataset visibility in the browser. The real 18-dataset/12-symbol-day corpus is confirmed present, untouched, at `apps/backend/.data/datasets/` (18 files, matches Build anchors' "12 symbol-days"), which is itself on the `STORE_SCOPE_PROTECTED_PATHS` list — correctly walled off from any browser-driven lane.
7. Cross-corroborated with UT-J-10: the shipped Referee Registry's Evidence Readiness panel (pre-existing, unrelated to this iteration's code) independently reports "0 tick dataset(s) are registered today" on this same rig — confirming the empty-corpus condition is a pre-existing, cross-cutting property of the shared fixture rig, not something newly introduced by this iteration's `micro_readiness.py`/frontend section.

**Expected:** The Microscope Readiness section shows the real legacy corpus: 12 distinct symbol-days, 18 shards each tagged `exploratory`/`hand_assigned`, session-equivalents ≈ 3.0, and 3 floor rows reading `floor_unmet` against the real 11-session availability.

**Actual:** The section shows an honest, correctly-wired, but EMPTY corpus (0/0/0.00/0.0000), because the mandated store-scoped QA backend has no tick-dataset fixtures — a pre-existing gap in a shared, cross-era test-infrastructure script, not a defect in this iteration's `micro_readiness.py`, `micro_routes.py`, or the new `/desk` frontend section. No implementation bug was found: every value that IS being served renders correctly, verbatim, with proper honest-empty-state copy, in the right place, with no console errors. Whether the real-corpus numeric acceptance is better verified via the backend's own unit/integration tests (this iteration's own TESTING REQUIREMENTS separately mandate exactly that: "`micro_readiness.py` against the REAL legacy corpus... a fixture cannot substitute for this check") or the shared fixture rig needs a tick-dataset seeding extension is a scope/policy call for the evaluator/auditor, not for browser-qa-agent to decide or fix.

No golden replay script was written for J-01 (only written for verified PASS journeys, per instructions).

---

## Skipped Tests

None — both journeys under test executed fully (frontend running, backend running, Chrome MCP available on the pinned :9222 profile throughout).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (store-scoped QA fixture rig — confirmed via `/research/desk/universe` `source_url: "fixture-rig"`)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned CDP port 9222, headless
- **Test Date:** 2026-08-17
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-1-evidence/`
- **Golden replay scripts:** `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` (lint-clean; J-01 skipped per FAIL)
