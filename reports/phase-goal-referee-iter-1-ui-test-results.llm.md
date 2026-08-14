# Goal Iteration goal-referee-iter-1 — UI Test Results

**Phase:** goal-referee-iter-1
**Date:** 2026-08-14
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. Some validation/regression/UX tests may have minor failures. -->
<!-- FAIL: Any smoke test fails, OR any happy-path test fails, OR any P1 test fails. -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable. ALL tests skipped. -->

**Overall:** 1/1 tests passed (0 skipped)

**Scope note:** Lean-mode dispatch for this iteration named exactly one journey to test here —
**J-01**. J-10 (required-still-passing) is explicitly excluded from this pass ("a deterministic
replay verifies them separately") and is already recorded PASS in
`reports/phase-goal-referee-iter-1-regression-replay-results.md` (demo_runner.py deterministic
replay of `runs/goal-session-referee/journey-scripts/J-10.json`, 1/1, screenshot
`reports/qa/goal-referee-iter-1-evidence/J-10-verify.png`). This report does not re-test J-10 and
claims no credit for that result.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — reconciliation made testable (evidence readiness fold) | smoke | P1 | `GET /research/desk/referee/evidence` live on the running QA-rig backend, HTTP 200, JSON matching the documented per-family readiness contract (`playbook_occurrence` + `strategy_trade`); `config_fingerprint` pin `08e471b10130e1e2` unchanged; `tick_gate_met` false with a non-empty `tick_gate_statement` naming the gate and shortfall; a non-empty `basis_caveats` entry naming the Card-6.4 `levels._bars_as_of` / `epoch <= as_of` forming-bar admission | Navigated to `http://localhost:8301/research/desk/referee/evidence` — HTTP 200, JSON rendered in-browser, byte-identical to a direct curl of the same URL. Full shape verified (see Passed Tests below); pin unchanged; TC-4's two exact-text requirements both satisfied | PASS | `reports/qa/goal-referee-iter-1-evidence/UT-J-01-result.png` |

---

## Passed Tests

### UT-J-01 — The era transition stands — reconciliation made testable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-1-evidence/UT-J-01-result.png`

**Journey nature and what this test actually checks:** goal.md tags J-01 `(Keyless; automated.)`
and its Acceptance line is entirely pytest-fixture-based ("on the fixture rig... hand-computed
fixture numbers exact"); the iteration spec's Definition of Done states explicitly "J-01 itself
needs NO browser check." There is zero frontend surface for this journey (no page, no nav
entry — `docs/handoffs/goal-referee-iter-1-dev.md` and the diff confirm this is a new backend
route only). Since the dispatch for this run still asked for a Chrome-MCP pass on J-01, the check
performed here is an honest **live-endpoint wiring and shape smoke-check via real browser
navigation** against the running QA-rig backend (`:8301`) — a genuine, non-fabricated
verification, but distinct from (and not a substitute for) J-01's official pytest-fixture-exact
acceptance, which lives in `apps/backend/tests/test_referee_evidence.py` and
`apps/backend/tests/test_referee_guards.py` (present on disk, outside this agent's remit to
execute).

**Steps taken:**
1. Navigated Chrome to `http://localhost:8301/research/desk/referee/evidence` (the endpoint
   `docs/goal.md`'s Data Contract and this iteration's spec both name).
2. Captured the rendered response body and cross-checked it against a direct `curl` of the same
   URL — byte-identical.
3. Verified the JSON shape against the iteration spec's documented Data Contract.

**What was observed (full body, HTTP 200):**
- `playbook_occurrence`: `detector_basis: "02bebbe17e7b8769"`,
  `config_fingerprint: "08e471b10130e1e2"` (unchanged pin), `records: 4`,
  `distinct_sessions: 3`, `signals_at_current_basis: 21`, `per_setup_side`: 7 entries, each
  `{setup, side, n, n_sessions}` — `capitulation/long`, `dbi/short`, `double_top/short`,
  `jbe/long`, `open_high_break/long` (n=14, n_sessions=3), `open_low_break/short`,
  `range_trade/long`. Plus an additive `integrity_errors: []`.
- `strategy_trade`: `dataset_count: 0`, `per_split_counts: {train: 0, holdout: 0}`,
  `trade_count: 0` — served honestly at HTTP 200, not 404/500, consistent with the desk router's
  never-404-on-absence convention. `tick_gate_met: false`.
  `tick_gate_statement`: *"the Era-6 tick-corpus gate (>= 150 symbol-days,
  docs/research-directions.md Card 5.2) is unmet: 0 tick dataset(s) are registered today, 150
  short of the gate."* — names both the gate and the measured shortfall (TC-4).
  `basis_caveats`: one entry naming `levels._bars_as_of` and the literal admission rule
  `epoch <= as_of` verbatim, matching TC-4's exact requirement for the Card-6.4 forming-bar
  disclosure. Plus an additive `integrity_errors: []`.
- Shape matches the iteration spec's Data Contract exactly, field-for-field (the two
  `integrity_errors: []` fields are additive honest-disclosure fields not named in the spec
  sample, not a contract deviation — flagging for the auditor's awareness, not treating as a
  defect).
- No console errors captured during navigation.

**Not verified by this agent (out of scope, by design):** the pytest-fixture-exact numeric
acceptance (TC-1 through TC-3, TC-5) against the committed hermetic corpora, the guard tests
(TC-6 through TC-8), the full backend suite count (TC-11), and the zero-diff/zero-new-Config-field
checks (TC-10) — all of these are pytest/static-analysis acceptance criteria with no browser
surface, already the developer/reviewer's responsibility per the existing
`apps/backend/tests/test_referee_evidence.py`, `apps/backend/tests/test_referee_guards.py`, and
`reports/reviews/goal-referee-iter-1-review.md` on disk.

---

## Failed Tests

None.

---

## Skipped Tests

None. (J-10 was not skipped by this agent — it was out of scope for this dispatch by explicit
instruction and is separately recorded PASS via deterministic replay; see Scope note above.)

---

## Golden Replay Script

No golden replay script was written for J-01. `scripts/automation/lib/demo_runner.py` resolves
every step's `goto` URL against a single `base_url` (the frontend origin), rewriting even
absolute `localhost` URLs onto that same host:port (`normalize_url`'s local-host-rewrite
behavior, confirmed by reading the function and its own test cases). J-01's only observable
surface is a backend-only JSON endpoint on a different port (`:8301`) with no frontend proxy —
confirmed by requesting the identical path against the frontend origin (`:3301`), which 404s
(Next.js's own not-found page, not the API response). A script for this journey would therefore
be un-replayable through the runner's single-base-url model; per the "best-effort" rule this
journey is skipped rather than written falsely. It falls back to an LLM browser-qa pass (or an
equivalent live-endpoint smoke check) next time, same as this run.

---

## Environment

- **Frontend URL:** http://localhost:3301 (HTTP 200; not exercised this run — J-01 has no
  frontend surface, and J-10, the only journey with one, was verified separately)
- **Backend URL:** http://localhost:8301 (the QA-rig backend actually exercised for UT-J-01)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned CDP
  port 127.0.0.1:9222, pump-launched headless instance (not launched or modified by this agent)
- **Test Date:** 2026-08-14
- **Evidence directory:** `reports/qa/goal-referee-iter-1-evidence/`
