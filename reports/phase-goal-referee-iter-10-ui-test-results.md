# UI Test Results (merged)

**Date:** 2026-08-15
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 16/16 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | The starter family — historical exploration becomes registered questions | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-10-evidence/J-07-verify.png |
| UT-01 | Desk page loads with all three Referee sections present | smoke | P1 | Desk title, 3-link nav, 3 collapsed Referee sections in order (Registry/Adjudications/Runs) | Confirmed via DOM: `desk-title`="Desk", nav = Cockpit/Structure/Desk, all 3 sections `aria-expanded="false"` with "▸" glyph in exact order, Runs last. No console errors. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-01-result.png` |
| UT-02 | Adjudications honest empty state (zero hypotheses) | smoke | P1 | Register disclosure + "No hypotheses registered." + no table | On a fresh zero-hypothesis fixture instance: register paragraph exact text present, `referee-adjudications-empty` shows "No hypotheses registered.", zero `referee-adjudications-table` elements. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-02-result.png` |
| UT-03 | Adjudications verdict chip + provenance per hypothesis | happy-path | P1 | S-1 row: verdict in vocabulary, uncolored chip, Status "N/12 sessions", Provenance 5 lines + BH, seed identity never em dash | S-1 row confirmed: verdict="registered" (neutral pill styling), Status="0 / 12 sessions", Provenance: `basis: —`, `null spec: referee-null-tod-v1`, `test spec: referee-test-perm-v1`, `seed identity: S-1` (value, not em dash), `attestation: —`, `BH: —`. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-03-result.png` |
| UT-04 | Populated panel shows `fragile` + refused-attestation entries | happy-path | P1 (fixture-dependent) | One row verdict=`fragile` w/ non-empty triggers; one row verdict=`insufficient_sample` w/ exact refusal text | Fixture seeded this run (see note above). QA-FRAGILE-1: verdict="fragile", triggers="cluster_ci_includes_zero". QA-REFUSED-1: verdict="insufficient_sample", Status text exactly "the checkpoint evaluation's oracle attestation is missing, mismatched, or version-stale -- confirmatory output is refused". Both visible alongside S-1 in one screenshot. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-04-result.png` |
| UT-05 | Referee Runs shows Null Builds + Evaluations sub-blocks | smoke | P1 | Both sub-headings, honest empty controls + empty ledgers | On zero-hypothesis instance: "Null Builds" + "No hypotheses registered — nothing to build a null for yet." + "No null-build runs recorded yet."; "Evaluations" + "No hypotheses registered — nothing to evaluate yet." + "No evaluation runs recorded yet." — all four texts confirmed. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-05-result.png` |
| UT-06 | Trigger button disables instantly on click | validation | P2 | Button `disabled` the instant it's clicked | Clicked "Evaluate" for S-1; the SAME captured DOM snapshot at click time shows `disabled=""` already present, label still "Evaluate" pending resolution. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-06-result.png` |
| UT-07 | Trigger + watch a null-build to completion (real write) | happy-path | P1 | Building… → live progress → completes → ledger row `completed` | Triggered "Build Null" for `referee-null-tod-v1` against the SCOPED fixture rig (verified via `assert_scoped_qa_backend.py` immediately before). Button disabled instantly, run completed (126/126), returned to idle "Build Null", ledger row appended with run_id/state=completed/timestamps. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-07-result.png` |
| UT-08 | Trigger + watch an evaluation to completion (real write) | happy-path | P1 | Evaluating… → live progress → completes → ledger row w/ terminal state | Triggered "Evaluate" for S-1 (SCOPED rig). Completed at 8/8, button re-enabled, ledger row `refereeevalrun-2026-08-15-f82bd2214d4d` shows hypothesis=S-1, state=completed, progress=8/8, started/finished ET timestamps, error=—. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-08-result.png` |
| UT-09 | Second in-flight trigger refused single-flight | error | P2 | No duplicate run; refusal surfaced | Two back-to-back UI clicks on the same control: 2nd click landed on an already-`disabled` button (no 2nd request dispatched) — the test's own documented fallback. Supplementary proof at the backend contract level: 5 truly-concurrent POSTs to `.../nulls/compute` yielded exactly ONE `started:true` and FOUR `started:false` (same compute id, `status:"running"`), confirming genuine single-flight refusal semantics; no duplicate ledger rows were ever created for a refused attempt. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-09-result.png` |
| UT-10 | Cancel an in-flight run (real write) | happy-path | P2 | Cancelling… → terminal non-completed state | This corpus's null-build completes in ~40ms, too fast for a natural UI double-round-trip to interrupt; used a calibrated concurrent start+cancel (sub-10ms offset) against the SAME scoped backend to reliably land the cancel mid-flight. Result: 7 genuinely-cancelled runs with real partial progress (e.g. 45/126, 1/126, 112/126) alongside completed ones in the SAME ledger; frontend renders `state`="cancelled" distinctly from "completed" (confirmed in rendered HTML and screenshot). | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-10-result.png` |
| UT-11 | Run ledger renders finished-run fields verbatim | happy-path | P1 | All columns verbatim; progress/error not sortable | Evaluate-runs and null-runs tables both show run/hypothesis-or-spec/state/progress/started/finished/error verbatim. `run_id`, `hypothesis_id`/`null_spec_id`, `state`, `started`, `finished` are sortable (`data-testid="desk-sort-header"`, clicking "started" flipped `aria-sort` none→ascending); `progress` and `error` headers carry no sort button/testid. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-11-result.png` |
| UT-12 | MCP: 22 tools, 2 new ones byte-identical to REST | regression | P2 | 22-tool list; byte-identical MCP vs curl, both fixture states | Verified in-process against the running rig (empty state on a disposable temp instance :8302, populated state on the live rig :8301): tool list = 22 entries incl. `desk_referee`/`desk_referee_registry`; both tools' `call_tool()` output byte-identical to `curl` in BOTH states (payload lengths matched exactly). Bonus: planted a corrupted `hypothesis-BROKEN.json` on the temp instance — both tools still returned the endpoint's own honest `integrity_errors` disclosure, byte-identical to curl, no exception. | PASS | non-browser; verification log in this report |
| UT-13 | Every pre-existing `/desk` section unaffected | regression | P1 | No visual shift / missing data on existing sections | Expanded Referee Registry (3-row Registered Hypotheses + 6-row shortlist, unchanged), Top-up Runs, Index Reconciliation, Screen Runs (honest empty states), Playbook Evidence (full signal table, basis block, band-location cohort, other-signatures list — all rendering real data). No "undefined"/"NaN"/`[object Object]` found on the page (checked programmatically; only false-positive substring hits inside Next.js's own internal RSC payload and the words "Provenance"/"Fragility"). | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-13-result.png` |
| UT-14 | Cockpit + Structure pinned-AAPL Load still work | regression | P1 | Both kept-product surfaces render without regression | Cockpit: watched SIM-BUYER, tape state reached "Buyer Control", chart/quote/features/trades/observations/event-log all populated. Structure: AAPL @ 2026-06-22 12:00:00 → Load rendered the tradable band map (candles + 8 resistance/support bands) and the case-studies table with real forward-return rows back to 2023 — matches prior iterations' pinned verification exactly. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-14-cockpit-result.png`, `reports/qa/goal-referee-iter-10-evidence/UT-14-structure-result.png` |
| UT-15 | New sections discoverable without prior knowledge | ux | P3 | Reachable via one scroll + one click, no hidden nav | Confirmed via UT-01's own navigation: "Referee Adjudications" sits directly below "Referee Registry" with no other page/menu involved, reached by scrolling to the bottom of `/desk` and a single header click. | PASS | `reports/qa/goal-referee-iter-10-evidence/UT-01-result.png` (shared) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-15


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | J-01 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-02 | J-02 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-03 | J-03 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-04 | J-04 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-05 | J-05 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-06 | J-06 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-08 | J-08 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
