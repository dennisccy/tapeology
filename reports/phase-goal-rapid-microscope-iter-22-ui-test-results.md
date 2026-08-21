# UI Test Results (merged)

**Date:** 2026-08-20
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 17/17 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-22-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-22-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-22-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-22-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-22-evidence/J-05-verify.png |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-22-evidence/J-08-verify.png |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-22-evidence/J-10-verify.png |
| UT-01 | `/desk` loads with Scout Ledger + Walk-Forward present | smoke | P1 | Page renders, both section headers visible, no console errors | Page rendered fully; `desk-section-expand-scoutLedger` and `desk-section-expand-walkForward` both present via selector query and visible in screenshot directly below "MICROSCOPE READINESS"; no console errors captured | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-01-result.png` |
| UT-02 | Study 1 screens and appears on `/desk` | happy-path | P1 | Family `failed_aggression_score__band_touch__trades_20` visible with trial row Feature `failed_aggression_score / threshold (band_touch)` and non-blank Decision | POST triggered run reached `state:"done"`; `GET /scout` showed the family; browser confirmed family block + trial row text `failed_aggression_score / threshold(band_touch)`, Decision `killed_insufficient_n` (non-blank) | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-02-result.png` |
| UT-03 | Study 3 screens and appears on `/desk` | happy-path | P1 | Family `failed_aggression_score__playbook_signal__trades_20` visible, Study 1 family still present (additive) | POST triggered run reached `state:"done"`; browser confirmed new family block, trial row Feature `failed_aggression_score / threshold(playbook_signal)`, non-blank Decision; Study 1's family block still visible in same ledger | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-03-result.png` |
| UT-04 | Both new studies record an honest floor-check row | validation | P1 | In both families, second row Feature/Horizon = `—`, Decision = `killed_insufficient_n` exactly; `screen_result` detail shows `null` | Both families' second rows confirmed: Feature/Horizon `— / —`, Decision `killed_insufficient_n`; opened the `<details>` for the floor-check row (band_touch family) and confirmed body text `null` | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-04-result.png` |
| UT-05 | Unrecognized `grid` value still 500s | error | P2 | HTTP 500; `/desk` unaffected on refresh | `curl` returned `500`; compute-manager state remained `done` (not stuck); `/desk` reloaded cleanly with no error banner | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-05-result.png` |
| UT-06 | "Run Screen" button still only runs the default grid | regression | P1 | Request body carries no `grid` field; new rows have no `(band_touch)`/`(playbook_signal)` suffix; no new `killed_insufficient_n`/`—` floor-check row | `fetch` monkey-patch showed the POST call's `opts.body` was `undefined` (no body/no grid field at all); run produced 3 new families (`cumulative_delta__none`, `failed_aggression_score__none`, `quote_imbalance__none`), all `structure_context.kind == "none"`, no `stage=="walkforward_floor_check"` row among them (confirmed via API + on-screen) | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-06-result.png` |
| UT-07 | Study 2's floor-check row still renders, freshly confirmed | regression | P1 | `divergence_at_level_bearish__band_touch__trades_20` family's second row shows `—`/`—`, Decision `killed_insufficient_n`, dated this iteration | Triggered a fresh `delta_divergence_pilot` run this session (registered timestamp `2026-08-20 18:47 ET`); family + floor-check row confirmed on screen, screenshot dated today | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-07-result.png` |
| UT-08 | J-07 Graduation surface unaffected, freshly confirmed | regression | P1 | HTTP 200; `families` non-empty with `family`/sealed reading (`verdict`,`rule_hash`)/`n`; unchanged shape | Browser navigated directly to `GET /research/desk/micro/graduation`; body rendered in Chrome's JSON viewer showing `family_root_id`, `sealed_evaluations[0].verdict:"pass"`, `rule_hash`, `n:30` | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-08-result.png` |
| UT-09 | Neither new study has an on-screen control | ux | P2 | Zero matches for both grid-selector strings anywhere on page; no dropdown/radio near "Run Screen" | Full-DOM text search: 0 hits for `range_wall_failed_aggression_pilot` and `capitulation_exhaustion_pilot`; 0 `<select>`/`input[type=radio]` elements anywhere on the whole page | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-09-result.png` |
| UT-10 | CLI path independently produces the same rows | smoke | P2 | stdout `1 candidate(s) processed`; on-disk ledger has screen row (closed-vocab decision, `structure_context.kind=="band_touch"`) + `walkforward_floor_check` row (`decision=="killed_insufficient_n"`) | Ran `.venv/bin/python -m app.research.scout --grid range_wall_failed_aggression_pilot` against fixture-pointed env-var dirs (scratchpad, never `.data/`); stdout matched exactly; on-disk `ledger.jsonl` held exactly 2 rows matching spec | PASS | `reports/qa/goal-rapid-microscope-iter-22-evidence/UT-10-ledger.jsonl` (terminal-only test; no browser surface) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-20

