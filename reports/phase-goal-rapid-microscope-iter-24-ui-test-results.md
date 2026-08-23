# UI Test Results (merged)

**Date:** 2026-08-23
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 13/16 journeys passed (2 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-24-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-24-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-24-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-24-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-24-evidence/J-05-verify.png |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-24-evidence/J-08-verify.png |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-24-evidence/J-10-verify.png |
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders, "Playbook Signals" visible, no console errors | Page rendered fully, "Playbook Signals" heading visible, no console errors captured | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-01-result.png` |
| UT-02 | Validation Vault section expands and shows shard rows | happy-path | P1 | Table `validation-vault-shards-table` appears with the 13 named column headers; ≥1 row with Universe=`iter18-qa-universe` | Table rendered with exactly those headers; 1 row present, Universe=`iter18-qa-universe` | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-02-result.png` |
| UT-03 | "Sealed at" column value check | regression | P1 | A bare calendar date, no time-of-day, no ET suffix (e.g. `2026-06-09`) | Backend serves `sealed_at: "2026-05-01"` (verified via `GET /research/desk/micro/vault`) but the page renders it as **`2026-04-30 20:00 ET`** — shifted one day earlier plus a spurious time, exactly the defect pattern the analysis predicted | FAIL | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-03-fail.png` |
| UT-04 | "Assigned at"/"Exposed at" unaffected | regression | P2 | Normal full date-time with ET suffix, e.g. `2026-06-09 14:32 ET` | Same row: Assigned at = `2026-06-04 20:00 ET`, Exposed at = `2026-06-05 20:00 ET` — both normal full date-times with ET suffix, contrasting correctly against the broken "Sealed at" cell | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-04-result.png` |
| UT-05 | Sealed rows stay opaque | validation | P1 | Every non-identity cell of a `sealed`-state row reads exactly `sealed — opaque` | Untestable — this scoped rig's Validation Vault currently contains exactly ONE shard, already in `exposed` state (confirmed via `GET /research/desk/micro/vault`: 1 shard total; `GET /research/desk/micro/readiness`: `sealed_tranche.shard_count: 0`). No row with State=`sealed` exists to inspect. | SKIP | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-05-skip.png` |
| UT-06 | Scout Ledger shows seeded pilot row | happy-path | P2 | Text `failed_aggression_score__playbook_signal__trades_20` visible; a closed-vocabulary decision (`killed_insufficient_n` expected) also visible | Both visible: family `failed_aggression_score__playbook_signal__trades_20 (root e47904f2f7f4f0e1)`, decision `killed_insufficient_n`, reason detail `n_candidate=0, n_comparator=1` | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-06-result.png` |
| UT-07 | Scout Ledger empty-state unchanged (ordinary backend) | error | P2 | "No candidates ledgered." visible against a fresh/empty ordinary backend | Not tested — this dispatch only has the scoped QA fixture rig running on :8301 (confirmed non-empty ledger, per UT-06). No ordinary/ambient backend instance is provisioned; ports 8000/8080/8300/3000 unreachable. Starting a second backend instance is outside this agent's scope (no app restart/infra management). | SKIP | none |
| UT-08 | Graduation fresh evidence | regression | P1 | Sealed-shard evidence identical to iter-22 (same universe id, same `exposed` state), with a screenshot dated 2026-08-23 or later | `iter18-qa-universe` shard present, State=`exposed`, Dataset/Family root/Symbol/Session date all disclosed exactly as before; screenshot file dated 2026-08-23 (today) | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-08-result.png` |
| UT-09 | Validation Vault discoverable | ux | P3 | Collapsed header "Validation Vault" reachable in one click; order Scout Ledger → Walk-Forward → Validation Vault | Confirmed via full-page capture and DOM extract: section order is Microscope Readiness → Scout Ledger → Walk-Forward → Validation Vault, unchanged; "Validation Vault" header visible without expanding any other section | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-09-result.png` |

## Failed Tests

### UT-03 — "Sealed at" column value check

**Verdict:** FAIL
**Failure:** Backend serves `sealed_at: "2026-05-01"` (verified via `GET /research/desk/micro/vault`) but the page renders it as **`2026-04-30 20:00 ET`** — shifted one day earlier plus a spurious time, exactly the defect pattern the analysis predicted
**Evidence:** ``reports/qa/goal-rapid-microscope-iter-24-evidence/UT-03-fail.png``

## Skipped Tests

### UT-05 — Sealed rows stay opaque

**Verdict:** SKIPPED
**Reason:** Untestable — this scoped rig's Validation Vault currently contains exactly ONE shard, already in `exposed` state (confirmed via `GET /research/desk/micro/vault`: 1 shard total; `GET /research/desk/micro/readiness`: `sealed_tranche.shard_count: 0`). No row with State=`sealed` exists to inspect.

### UT-07 — Scout Ledger empty-state unchanged (ordinary backend)

**Verdict:** SKIPPED
**Reason:** Not tested — this dispatch only has the scoped QA fixture rig running on :8301 (confirmed non-empty ledger, per UT-06). No ordinary/ambient backend instance is provisioned; ports 8000/8080/8300/3000 unreachable. Starting a second backend instance is outside this agent's scope (no app restart/infra management).

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-23

