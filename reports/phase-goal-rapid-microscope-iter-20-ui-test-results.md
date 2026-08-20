# UI Test Results (merged)

**Date:** 2026-08-20
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 3/3 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-20-evidence/J-08-verify.png |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-20-evidence/J-10-verify.png |
| UT-J-07 | Graduation — provenance in, nothing laundered out | regression (evidence re-check) | P1 | Fresh browser navigation directly to the scoped backend's `GET /research/desk/micro/graduation` returns HTTP 200 with a non-empty, discriminating body: `families` array of length 1, single entry `verdict: "pass"`, `n: 30`, `rule_hash` starting `8aaea80b`; `floors_applied` matches the on-disk ledger row byte-for-byte; no vault secret in the capture | Navigated Chrome (via CDP, `mcp__plugin_superpowers-chrome_chrome__use_browser`) directly to `http://localhost:8301/research/desk/micro/graduation` (port 8301 read from `reports/qa-scoped-backend-store-manifest.md`'s `port:` line for the launch timestamped `launched_at_utc: 2026-08-20T15:56:30Z`). Browser rendered Chrome's built-in JSON viewer showing exactly one family (`family_root_id: "240dd966c1aceca2"`, state `exploratory`) with one `sealed_evaluations` entry: `verdict: "pass"`, `n: 30`, `rule_hash: "8aaea80b53c56805a396a3f8456ae79702e6527b8b4c9aeb5f009a54ff58d115"`, `floors_applied: {min_observations: 30, min_signal_sessions: "not_applicable_single_shard", min_symbols: "not_applicable_single_shard"}`, `chain_verification.ok: true`. `extract` (page text) captured the identical raw JSON. Cross-checked the on-disk ledger row (`.../tapeology-store-scope-qa/rig/micro_graduation/graduation_ledger.jsonl`, located via the same manifest's store root, matched by `row_hash`) — `rule_hash`, `floors_applied`, `verdict`, and `n` are byte-for-byte identical to the captured body. Independently recomputed `sealed_pass_rule_hash()` fresh from the shipped `apps/backend/app/research/micro_sealed_evaluation.py` source under the scoped rig's env — result `8aaea80b53c56805a396a3f8456ae79702e6527b8b4c9aeb5f009a54ff58d115`, matching both the captured body and the ledger row. No occurrence of a vault-secret-shaped string anywhere in the screenshot or the extracted JSON text — only ordinary content hashes (`row_hash`, `rule_hash`, `shard_checksum`, `spec_hash`) appear, all clearly derived/commitment-style values, never a raw secret. Console-error check: the Chrome MCP tool's own `enable_console_logging`/`get_console_messages` reported "No console messages captured" and the auto-captured `*-console.txt` file literally states `# TODO: Console logging not yet implemented` — this is a known tool-level limitation, not a verified zero-error state; noted honestly below rather than claimed as a hard pass. The page itself is Chrome's native JSON viewer over a bare `application/json` response with no page-level JS to error. | PASS | `reports/qa/goal-rapid-microscope-iter-20-evidence/J-07-graduation.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-20

