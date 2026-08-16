# UI Test Results (merged)

**Date:** 2026-08-16
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 5/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | The starter family — historical exploration becomes registered questions | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-12-evidence/J-07-verify.png |
| UT-J-09 | The Referee on /desk + MCP contract v5 — 22 read-only tools | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-12-evidence/J-09-verify.png |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-12-evidence/J-10-verify.png |
| UT-J-05 | The registry — pre-registration with an immutable boundary | regression | P1 | The shipped Referee Registry section's "Registered Hypotheses" table renders a real append-only hypothesis record with its immutable boundary date, origin label, status, and accrual — the UI-observable face of J-05's registry (full backend acceptance — append-only proof, duplicate/retroactive-boundary refusal, ET-midnight boundary case — is covered by the automated backend suite per J-05's own "(Keyless; automated.)" tag) | Expanded "Referee Registry" on `/desk`; "Registered Hypotheses" table showed one row: S-1 \| capitulation:long \| 2026-08-15 \| historical-exploration \| active \| 0 / 12 \| 1 / 1 discovery (exploratory). Shortlist row for S-1 shows Action="Registered" (disabled), distinct from "Select" on S-2..S-6 — consistent with single-registration, append-only behavior | PASS | `reports/qa/goal-referee-iter-12-evidence/UT-J-05-result.png` |
| UT-J-11 | The accrual projection states its own basis — the wait, measured in recorded sessions | feature | P1 | On `/desk`'s Referee Registry section: one descriptive basis line (recorded sessions, pooled sessions, span days, first→last date, longest zero-session stretch) renders above the shortlist table, and one new right-aligned column renders beside the shipped "Projected days" column — both read verbatim from the API (zero client arithmetic) — while the shipped `accrual_rate_sessions_per_day`/`projected_days_to_target` and every other shipped `/desk` section render exactly as shipped in the same pass | Basis line (`referee-accrual-basis-line`) rendered "Recorded sessions 3 · pooled at the current detector basis 3 · corpus span 47d (2026-06-22 → 2026-08-07) · longest zero-session stretch 42d (2026-06-25 → 2026-08-07)" — byte-identical to a direct `GET /research/desk/referee/registry/shortlist` cross-check. New "Projected sessions" column sits immediately right of "Projected days"; S-1/S-2/S-3 show "36" (== target_sessions 12 / rate 0.333 exactly, matching the live API's `projected_pooled_sessions_to_target`); S-4/S-5/S-6 show "—" (API `null`, zero-rate divide-by-zero discipline). Shipped "Accrual / day" (0.02) / "Projected days" (564) unchanged. Every other shipped section visible in the same pass (Desk screen, Playbook Signals, Backscan, collapsed Top-up/Index/Screen Runs, Playbook Evidence, Referee Adjudications header) rendered with no corruption | PASS | `reports/qa/goal-referee-iter-12-evidence/UT-J-11-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-16

