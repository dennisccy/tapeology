# Goal Iteration 20 — UI Test Results (LLM browser-qa-agent)

**Phase:** goal-rapid-microscope-iter-20
**Date:** 2026-08-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

Scope note: this is a `Depth: evidence` re-verification round per the iter spec. Only J-07 was
dispatched to this agent (fresh, non-golden LLM-driven capture). J-08 and J-10 are verified
separately this iteration via their stored golden replay scripts by the deterministic replay
runner — see `reports/phase-goal-rapid-microscope-iter-20-regression-replay-results.md`
(2/2 PASS: UT-J-08, UT-J-10) — and were NOT re-driven by this agent, per dispatch instructions.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | Graduation — provenance in, nothing laundered out | regression (evidence re-check) | P1 | Fresh browser navigation directly to the scoped backend's `GET /research/desk/micro/graduation` returns HTTP 200 with a non-empty, discriminating body: `families` array of length 1, single entry `verdict: "pass"`, `n: 30`, `rule_hash` starting `8aaea80b`; `floors_applied` matches the on-disk ledger row byte-for-byte; no vault secret in the capture | Navigated Chrome (via CDP, `mcp__plugin_superpowers-chrome_chrome__use_browser`) directly to `http://localhost:8301/research/desk/micro/graduation` (port 8301 read from `reports/qa-scoped-backend-store-manifest.md`'s `port:` line for the launch timestamped `launched_at_utc: 2026-08-20T15:56:30Z`). Browser rendered Chrome's built-in JSON viewer showing exactly one family (`family_root_id: "240dd966c1aceca2"`, state `exploratory`) with one `sealed_evaluations` entry: `verdict: "pass"`, `n: 30`, `rule_hash: "8aaea80b53c56805a396a3f8456ae79702e6527b8b4c9aeb5f009a54ff58d115"`, `floors_applied: {min_observations: 30, min_signal_sessions: "not_applicable_single_shard", min_symbols: "not_applicable_single_shard"}`, `chain_verification.ok: true`. `extract` (page text) captured the identical raw JSON. Cross-checked the on-disk ledger row (`.../tapeology-store-scope-qa/rig/micro_graduation/graduation_ledger.jsonl`, located via the same manifest's store root, matched by `row_hash`) — `rule_hash`, `floors_applied`, `verdict`, and `n` are byte-for-byte identical to the captured body. Independently recomputed `sealed_pass_rule_hash()` fresh from the shipped `apps/backend/app/research/micro_sealed_evaluation.py` source under the scoped rig's env — result `8aaea80b53c56805a396a3f8456ae79702e6527b8b4c9aeb5f009a54ff58d115`, matching both the captured body and the ledger row. No occurrence of a vault-secret-shaped string anywhere in the screenshot or the extracted JSON text — only ordinary content hashes (`row_hash`, `rule_hash`, `shard_checksum`, `spec_hash`) appear, all clearly derived/commitment-style values, never a raw secret. Console-error check: the Chrome MCP tool's own `enable_console_logging`/`get_console_messages` reported "No console messages captured" and the auto-captured `*-console.txt` file literally states `# TODO: Console logging not yet implemented` — this is a known tool-level limitation, not a verified zero-error state; noted honestly below rather than claimed as a hard pass. The page itself is Chrome's native JSON viewer over a bare `application/json` response with no page-level JS to error. | PASS | `reports/qa/goal-rapid-microscope-iter-20-evidence/J-07-graduation.png` |

---

## Passed Tests

### UT-J-07 — Graduation — provenance in, nothing laundered out
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-20-evidence/J-07-graduation.png`

- **Store provenance (per the iter-18 lesson — cited by path, not asserted from shell):** the
  scoped backend serving this capture is documented in
  `reports/qa-scoped-backend-store-manifest.md`, launched at `2026-08-20T15:56:30Z`, root
  `/home/dennis-chan/.cache/iad/iad.goal-rapid-m-33532ec4.2777839/tapeology-store-scope-qa/rig`,
  port `8301`. This report cites that file rather than re-deriving or asserting "real data
  store" independently.
- **TC-1 (fresh capture, discriminating body):** HTTP navigation to
  `http://localhost:8301/research/desk/micro/graduation` returned `families` array length 1,
  entry `verdict: "pass"`, `n: 30`, `rule_hash` starting `8aaea80b` — all satisfied, verified
  both via the browser's rendered JSON viewer (screenshot) and the `extract` page-text capture.
- **TC-2 (floors_applied match, byte-for-byte, and rule_hash freshness):** the captured
  `floors_applied` (`min_observations: 30`, `min_signal_sessions:
  "not_applicable_single_shard"`, `min_symbols: "not_applicable_single_shard"`) was diffed
  against the on-disk ledger row in
  `.../rig/micro_graduation/graduation_ledger.jsonl` (located under the scoped rig documented
  by the manifest) — identical, byte for byte. `sealed_pass_rule_hash()` was also recomputed
  fresh from the currently shipped `micro_sealed_evaluation.py` source
  (`.venv/bin/python -c "from app.research.micro_sealed_evaluation import
  sealed_pass_rule_hash; print(sealed_pass_rule_hash())"`) and produced the identical
  `8aaea80b53c56805a396a3f8456ae79702e6527b8b4c9aeb5f009a54ff58d115`.
- **TC-3 (console errors):** NOT independently confirmable this round — the Chrome MCP tool's
  console-capture path is unimplemented (`# TODO: Console logging not yet implemented` in its
  own auto-captured log; `get_console_messages` returned no messages either way). This is a
  tooling gap, not evidence of either presence or absence of errors. The endpoint under test is
  a bare JSON response with no client-side JS to throw, which limits the practical risk, but the
  claim is recorded honestly as unconfirmed rather than asserted PASS.
- **TC-4 (store citation by path):** satisfied — see the "Store provenance" bullet above; this
  report never asserts "real data store" from an uninspected shell.
- **TC-7 (vault secret absence):** confirmed absent from both the screenshot and the extracted
  JSON text — the response contains only derived hashes (`row_hash`, `rule_hash`,
  `shard_checksum`, `spec_hash`, `dataset_id`), none of which is the vault secret file's
  contents; only sha256-style commitments appear anywhere in the capture.

**Golden replay script:** intentionally NOT authored for J-07 this iteration — per the iter
spec's explicit "OUT OF SCOPE" list and the iter-19 lesson it cites verbatim:
`normalize_url()` rewrites any localhost URL onto the frontend base, no `/research/*` proxy
exists on the frontend, and `/desk` renders zero graduation content, so a stored replay script
cannot reach this endpoint. The LLM browser-qa lane navigating directly to the backend's own
port (as done here) is the correct and only lane for J-07 by design; this round did not attempt
to change that.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-08 and J-10 were not driven by this agent by design (explicitly excluded from this
dispatch — verified separately via stored golden replay scripts; see
`reports/phase-goal-rapid-microscope-iter-20-regression-replay-results.md`).

---

## Environment

- **Frontend URL:** http://localhost:3301 (not exercised this round — J-07 is a direct backend
  navigation per the iter spec; frontend confirmed reachable, HTTP 200, as a precondition check
  only)
- **Backend URL (J-07 target):** http://localhost:8301 (scoped QA rig; see
  `reports/qa-scoped-backend-store-manifest.md`)
- **Browser:** Headless Chrome via CDP (`mcp__plugin_superpowers-chrome_chrome__use_browser`),
  pinned profile on port 9222 (pre-launched by the pump; not started or altered by this agent)
- **Test Date:** 2026-08-20
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-20-evidence/`
