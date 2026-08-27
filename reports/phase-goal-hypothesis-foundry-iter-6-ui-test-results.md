# UI Test Results (merged)

**Date:** 2026-08-27
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 13/13 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The Foundry opens as a new finite era and the old self-extension loop is inactive | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-01-verify.png |
| UT-J-02 | Ratified sources compile into auditable CandidateSpecs or typed blocks without outcome input | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-02-verify.png |
| UT-J-03 | Generic interpretation preserves timing, population symmetry, direction, and exact Scout decisions | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-03-verify.png |
| UT-J-04 | Foundry owns the denominator, append-only state, freeze barrier, and integrity lock | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-04-verify.png |
| UT-J-05 | The complete factory passes hermetic known-null, planted-effect, leakage, and honest-stop oracles | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-05-verify.png |
| UT-J-06 | The real epoch: source registry, manifest, and Git-visible freeze | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-06-verify.png |
| UT-01 | `/desk` loads, Hypothesis Foundry panel present | smoke | P1 | Page renders, "Hypothesis Foundry" heading present (collapsed), no console errors, no `foundry-panel-unavailable` element | Page rendered fully; `[data-testid="desk-section-expand-hypothesisFoundry"]` found with text "▸Hypothesis Foundry"; `foundry-panel-unavailable` absent; console showed only the benign React DevTools info line | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-01-result.png` |
| UT-02 | Runner / Checkpoint shows the real exhaust state | happy-path | P1 | All 9 `foundry-runner-*` fields show the exact real values from `exhaust_progress`; empty/incomplete states absent | Every field matched verbatim (see detail below); `foundry-runner-checkpoint-empty` and `foundry-runner-exhaust-incomplete` both absent | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-02-result.png` (clean full capture, scrollY 0, enlarged viewport) |
| UT-03 | Every field is a real value, no placeholder leakage | validation | P2 | On-screen text is a byte-identical, unformatted echo of the API JSON; protected-read-count and freeze-integrity-verdict render `text-emerald-400`, not `text-rose-400` | `curl` of `GET /research/desk/micro/foundry` compared field-by-field against on-screen `eval` text — identical; `outerHTML` confirmed both lines use `class="font-mono text-emerald-400"`; hash shown full-length (64 hex chars), not truncated | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-03-result.png` |
| UT-04 | Backend outage shows honest error, not a crash | error | P2 | `foundry-panel-unavailable` appears with honest error text; rest of `/desk` stays functional; no fabricated `exhaust_progress` values | Simulated via a `window.fetch` override scoped to `*/research/desk/micro/foundry*` (see note below on tooling) + SPA remount: showed `foundry-panel-unavailable` = "Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place."; no "Era-Open Baseline" / "0 of 0" anywhere; Desk Screen, Playbook, Backscan sections above it stayed fully visible and interactive | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-04-result.png` (clean full capture) |
| UT-05 | Sibling subsections unchanged | regression | P2 | Sources/Compiler, Interpreter Fixtures, Freeze/Integrity, Hermetic Oracles show their pre-existing text unchanged; no new `exhaust_progress`-related field leaks into them | All 4 confirmed present via DOM text; grep of every `[data-testid]` on the page for `foundry-runner` found only the legitimate `desk-section-expand-foundry-runner-checkpoint-section` header button — no leakage | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-05-result.png` (partial/best-effort capture — see note) |
| UT-06 | J-01..J-06 golden journeys replay clean | regression | P1 | All six journeys' exact assertions still hold | `08e471b10130e1e2` (J-01) present; "Era-Open Baseline" + "Hashes match — outcome-blind compilation proven." (J-02) present; "BLOCKED_UNSUPPORTED_RELATION" (J-03) present; "docs/hypothesis-foundry/freeze-set.json" (J-04) present; "Protected-data trip fails closed / evidence class immutable" (J-05) present; `epoch:afd19e9c11a6534f` (J-06) present | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-06-result.png` (partial/best-effort capture — see note) |
| UT-07 | Runner / Checkpoint discoverable in 2 clicks | ux | P3 | Reached in exactly 2 clicks; label unambiguous, sits below Epoch/Manifest; no duplicate rendering elsewhere | Fresh navigation → click `hypothesisFoundry` (1) → click `foundry-runner-checkpoint-section` (2) → target visible and populated; DOM order confirms `...epoch-manifest-section, runner-checkpoint-section` (Runner/Checkpoint immediately follows Epoch/Manifest); zero other occurrences of "Checkpoint: 0 of 0" text anywhere on the page | PASS | `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-07-result.png` (clean full-page capture) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-27

