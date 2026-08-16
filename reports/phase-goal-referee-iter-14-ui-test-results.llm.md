# Goal Iteration 14 (goal-referee) — UI Test Results

**Phase:** goal-referee-iter-14
**Date:** 2026-08-16
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 4/4 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — reconciliation made testable | keyless | P1 | `apps/backend/tests/test_referee_guards.py` run to completion, all collected tests pass (iter-13 live count: 19) | `19 passed in 0.16s`, 0 failures | PASS | none (backend-only journey, `(Keyless; automated.)` per goal.md — no browser surface exists) |
| UT-J-02 | The evidence contract — two families, one observation shape | keyless | P1 | `apps/backend/tests/test_referee_evidence.py` run to completion, all collected tests pass (iter-13 live count: 29) | `29 passed in 2.48s`, 0 failures | PASS | none (backend-only journey, `(Keyless; automated.)` per goal.md — no browser surface exists) |
| UT-J-05 | The registry — pre-registration with an immutable boundary | regression | P1 | Referee Registry panel expand renders the S-1 hypothesis row (`historical-exploration` origin, `2026-08-15` boundary, `active` status) | Live-driven re-check (fresh nav, timed click→text-found ≈3.06s, well inside the golden's 12s budget) confirms `S-1 / capitulation:long / 2026-08-15 / historical-exploration / active / 0 / 12 / 1 / 1 discovery (exploratory)` all render correctly | PASS | `reports/qa/goal-referee-iter-14-evidence/UT-J-05-result.png` |
| UT-J-12 | The readiness fold gets its reader — why a family cannot speak, visible on the desk | evidence | P1 | An in-frame, legible capture of the `referee-evidence-strategy-block` element (tick-gate sentence + every basis-caveats entry), checksum-distinct from iter-13's `J-12-seeded-rig-result.png`, `J-12-empty-corpus-result.png`, and `J-05-result.png` | Element captured with both `referee-evidence-strategy-tick-gate` and `referee-evidence-strategy-basis-caveats` fully legible; SHA-256 confirmed distinct from all three named iter-13 files | PASS | `reports/qa/goal-referee-iter-14-evidence/J-12-strategy-block-result.png` |

---

## Passed Tests

### UT-J-01 — The era transition stands — reconciliation made testable
**Verdict:** PASS
**Evidence:** none (backend-only; journey is marked `(Keyless; automated.)` in goal.md, and its golden-script slot is `journey-scripts/J-01.json.invalid` by design — there is no browser surface to screenshot)
- Ran `apps/backend/.venv/bin/python -m pytest tests/test_referee_guards.py -v` from `apps/backend/`. Collected 19 items, all 19 passed, 0 failed, in 0.16s. This matches iteration 13's live-run count exactly (reconfirmed live, not carried forward unverified per the iteration spec's instruction). Replaces the prior `DEFERRED-BUDGET` row with a real PASS.

### UT-J-02 — The evidence contract — two families, one observation shape
**Verdict:** PASS
**Evidence:** none (backend-only; journey is marked `(Keyless; automated.)` in goal.md, golden-script slot is `journey-scripts/J-02.json.invalid` by design)
- Ran `apps/backend/.venv/bin/python -m pytest tests/test_referee_evidence.py -v` from `apps/backend/`. Collected 29 items, all 29 passed (2 unrelated deprecation warnings from `starlette`/`websockets` libraries, no test failures), in 2.48s. Matches iteration 13's live-run count exactly. This run also re-exercises the three J-01-labeled readiness-fold tests (`test_playbook_readiness_pools_newest_per_date_at_the_current_basis`, `test_strategy_readiness_counts_datasets_splits_and_trades`, `test_strategy_readiness_names_the_unmet_tick_gate_and_the_forming_bar_caveat`) inside this same module, so no separate slice run was needed. Replaces the prior `DEFERRED-BUDGET` row with a real PASS.

### UT-J-05 — The registry — pre-registration with an immutable boundary
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-14-evidence/UT-J-05-result.png`
- **Context:** the automated deterministic replay (`demo_runner.py --mode verify`, output at `reports/phase-goal-referee-iter-14-regression-replay-results.md`) had already run before this dispatch and recorded J-05 as FAIL: "step 02 expected 'historical-exploration' did not appear" within the script's 12000ms budget. Per the dispatch's explicit instruction, this journey was escalated to me for live re-verification rather than accepted as a regression.
- Navigated fresh to `/desk` (clean page load, no prior session state reused), clicked `[data-testid="desk-section-expand-refereeRegistry"]`, then used `await_text("historical-exploration", timeout: 30000)` while bracketing the call with wall-clock timestamps. Click-return to text-found elapsed ≈3.06s — comfortably inside the golden script's 12s budget, not near the edge.
- Inspected the live DOM text around the found string: `S-1capitulation:long2026-08-15historical-explorationactive0 / 121 / 1 discovery (exploratory)` — i.e., the Registered Hypotheses table's S-1 row carries `capitulation:long` setup/side, `2026-08-15` boundary, `historical-exploration` origin, `active` status, `0/12` accrual, `1/1 discovery (exploratory)` — exactly the fields TC-6 names as iteration 13's recorded values, with no drift.
- Captured a full-page screenshot and cropped to the Registered Hypotheses table region (technique note below); the resulting image shows the S-1 row with all fields legible.
- **Assessment:** the underlying page content is correct and stable; the replay's FAIL reads as a timing false-negative (most likely a cold-cache first-hit against the Referee Registry panel's three server requests, since J-05 runs first in that replay's journey order while J-07/09/10/11 — run afterward against an already-warmed backend — all passed in the same replay pass). This matches the pattern the pump note already flagged as "watch, don't act": the panel's request count and wait budget are a carried observation, not something this dispatch authorized fixing. I did not modify `journey-scripts/J-05.json` (its steps and expectations are already correct; the flakiness is server-side latency variance, not a selector or expectation defect the script controls) and did not touch the panel's request count or any timeout, consistent with this iteration's explicit out-of-scope item.

### UT-J-12 — The readiness fold gets its reader — why a family cannot speak, visible on the desk
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-14-evidence/J-12-strategy-block-result.png`
- Navigated to `/desk`, clicked `[data-testid="desk-section-expand-refereeRegistry"]`, waited for "Strategy Family" text. Confirmed via `extract` over `[data-testid="referee-evidence-strategy-block"]` that the live DOM carries real, non-empty content: the Datasets/Train-Holdout/Trades table (all 0, honest empty-corpus counts), the `referee-evidence-strategy-tick-gate` sentence ("the Era-6 tick-corpus gate (>= 150 symbol-days, docs/research-directions.md Card 5.2) is unmet: 0 tick dataset(s) are registered today, 150 short of the gate."), the full `referee-evidence-strategy-basis-caveats` forming-bar disclosure paragraph, and "No integrity errors."
- **Capture technique note (relevant finding, not a product defect):** a plain viewport screenshot after scrolling the element into view (via both JS `scrollIntoView` and the tool's native CDP-level `scroll` action, at two different viewport heights) reproducibly rendered blank or visibly wrong content (a duplicated/mispositioned sticky-nav artifact), even though the DOM/layout state was independently confirmed correct via `eval`/`extract` at the same moment — a headless-Chrome compositor/raster desync specific to large programmatic scroll jumps on this tall page, not a real rendering bug in the product. Workaround: this session's total page height (`document.documentElement.scrollHeight`) was 4103px — under the tool's 4320px fullpage-capture cap (unlike iteration 13's attempt, whose page state was evidently taller) — so a `fullpage: true` capture rendered every section correctly in one pass, including the target block. I then cropped that fullpage image tightly to the `referee-evidence-strategy-block` element's own bounding box (`getBoundingClientRect()`: offsetTop 3470, height 444, ±15px margin), producing an element-scoped image from unmodified, real pixels.
- Verified the resulting image shows both `referee-evidence-strategy-tick-gate` and every `referee-evidence-strategy-basis-caveats` entry fully in-frame and legible (visually confirmed via direct image read).
- Hash-checked: SHA-256 of the new capture (`e3925b4...`) differs from all three named iteration-13 files — `J-05-result.png` (`6d145a3e...`), `J-12-seeded-rig-result.png` (`6d145a3e...` — **identical to `J-05-result.png`, confirming the pump note's suspicion that iter-13's "seeded rig" capture was in fact a duplicate/truncated shot that never reached the Strategy Family block**), and `J-12-empty-corpus-result.png` (`22f3ac2c...`).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (fixture-scoped rig confirmed via `assert_scoped_qa_backend.py` → `SCOPED`, `source_url='fixture-rig-iter8-replay'`, exit 0)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), attached to the pump-launched isolated headless Chrome on CDP `127.0.0.1:9222` — no browser launched or killed by this agent
- **Test Date:** 2026-08-16
- **Evidence directory:** `reports/qa/goal-referee-iter-14-evidence/`
- **No `/desk` Referee write control was exercised** (no Build Null / Evaluate / Register Hypothesis / Withdraw / compute / cancel click) — every check in this run was a pure read over already-recorded stores, per the dispatch guardrail.

## Notes on journeys not in this dispatch's scope

Per explicit dispatch instruction ("Do NOT test these — a deterministic replay verifies them separately: J-05 J-07 J-09 J-10 J-11"), J-07, J-09, J-10, and J-11 were not driven by this agent. Their re-verification was already completed by the deterministic replay pass before this dispatch began (`reports/phase-goal-referee-iter-14-regression-replay-results.md`, written 2026-08-16 by `demo_runner.py --mode verify`): J-07 PASS, J-09 PASS, J-10 PASS, J-11 PASS (J-05 recorded FAIL there — superseded by this report's live re-verification above, which found no product regression).

No golden replay script was added or modified this run: `journey-scripts/J-05.json` and `journey-scripts/J-12.json` already existed and their steps/selectors/expectations are exactly what this session's live drive exercised and confirmed correct, so there was nothing to change. `journey-scripts/J-01.json.invalid` and `J-02.json.invalid` remain untouched by design (no browser surface to script).
