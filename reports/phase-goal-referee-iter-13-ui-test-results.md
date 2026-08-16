# UI Test Results (merged)

**Date:** 2026-08-16
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 6/6 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | The registry — pre-registration with an immutable boundary | regression | P1 | Expanding "Referee Registry" on `/desk` shows the Registered Hypotheses table with hypothesis S-1's `origin` reading `historical-exploration` (this iteration's deterministic replay reported this text absent — flagged for direct LLM re-verification) | Navigated `/desk`, clicked `desk-section-expand-refereeRegistry`. Registered Hypotheses table renders row S-1 (`capitulation:long`, boundary `2026-08-15`, origin `historical-exploration`, status `active`, accrual `0/12`, discovery `1/1`) — confirmed via full HTML DOM extraction (raw `<td>` text) and a full-page screenshot. Text genuinely present and correctly rendered; the replay tool's FAIL was a false negative (see Notes) | PASS | `reports/qa/goal-referee-iter-13-evidence/J-05-result.png` |
| UT-J-07 | The starter family — historical exploration becomes registered questions | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-13-evidence/J-07-verify.png |
| UT-J-09 | The Referee on /desk + MCP contract v5 — 22 read-only tools | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-13-evidence/J-09-verify.png |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-13-evidence/J-10-verify.png |
| UT-J-11 | The accrual projection states its own basis — the wait, measured in recorded sessions | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-13-evidence/J-11-verify.png |
| UT-J-12 | The readiness fold gets its reader — why a family cannot speak, visible on the desk | happy-path | P1 | On the seeded fixture rig, the new Evidence Readiness blocks (Playbook Family + Strategy Family) render every value string-for-string identical to that same request's own `GET /research/desk/referee/evidence` body; on a SEPARATE empty-corpus backend, both blocks render an honest all-zero/absent state, never blank/spinner/404 | Seeded rig (`fixture-rig-iter8-replay`, :3301/:8301): Playbook Family showed `records=4, distinct_sessions=3, signals_at_current_basis=21`, `detector_basis=02bebbe17e7b8769`, `config_fingerprint=08e471b10130e1e2`, "No stale basis dates.", "No integrity errors."; Strategy Family showed `Datasets=0, Train/Holdout=0/0, Trades=0`, the full tick-gate-unmet sentence, and the Card-6.4 basis caveat — all byte-matched against a same-moment `curl` of the live endpoint. Built an isolated empty-corpus backend+frontend pair (:8302/:3302, fresh store dirs) and confirmed via `curl` the served body was genuinely all-zero before use; navigated, expanded Referee Registry: Playbook Family all-zero, Registered Hypotheses showed "No hypotheses registered.", Strategy Family all-zero with the same tick-gate/caveat text still present (not corpus-dependent), no blank/spinner/404 anywhere. Console clean on both passes | PASS | `reports/qa/goal-referee-iter-13-evidence/J-12-seeded-rig-result.png`, `reports/qa/goal-referee-iter-13-evidence/J-12-empty-corpus-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-16


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | J-01 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-02 | J-02 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
