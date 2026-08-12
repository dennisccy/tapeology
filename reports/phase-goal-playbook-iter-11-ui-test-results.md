# UI Test Results (merged)

**Date:** 2026-08-12
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-11-evidence/J-01-verify.png |
| UT-J-02 | Every signal measured — the rail's own conventions, anchored at the trigger bar | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-11-evidence/J-02-verify.png |
| UT-J-03 | The Playbook lands on /desk | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-11-evidence/J-03-verify.png |
| UT-J-04 | The continuation family — JBE, DBI, cup-and-handle | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-11-evidence/J-04-verify.png |
| UT-J-05 | The climax family — capitulation entry, euphoria marker | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-11-evidence/J-05-verify.png |
| UT-J-06 | The range family — range trades, double top/bottom | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-11-evidence/J-06-verify.png |
| UT-J-07 | The back-scan — every recorded session, resumable and append-only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-11-evidence/J-07-verify.png |
| UT-J-08 | The evidence view — distributions beside the null, min-n honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-11-evidence/J-08-verify.png |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-11-evidence/J-10-verify.png |
| UT-J-09 | MCP contract v4 — 20 read-only tools | integration (live registry, keyless) + browser (golden shell-string regression) | P1 | Live `app.mcp` tool registry advertises exactly 20 tools; `desk_playbook` and `desk_playbook_evidence` present by name; `/desk` renders the Playbook Evidence section's static "Built from signature:" label (the data-contract row the new tools proxy); a lint-clean golden replay script exists for future re-verification | Live import of `app.mcp.list_tools()` returned exactly 20 tools matching `EXPECTED_TOOLS`/`TOOL_NAMES` byte-for-byte, both `desk_playbook`/`desk_playbook_evidence` present at positions 15/16. Navigated to `http://localhost:3301/desk` on the confirmed scoped fixture rig (`fixture-rig-iter8-replay`, 20 members); Playbook Evidence section rendered `"Built from signature: 9ba29d8e3aaaa643"` (DOM `extract` verbatim match on the label). Screenshot captured. New golden `runs/goal-session-playbook/journey-scripts/J-09.json` authored and passes `demo_runner.py --mode lint`. No console errors (only the standard React DevTools info line). | PASS | `reports/qa/goal-playbook-iter-11-evidence/UT-J-09-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-12

