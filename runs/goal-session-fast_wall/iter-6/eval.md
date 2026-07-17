# Iteration 6 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** n/a (halting — goal achieved; if resumed for enhancement, lean)

## Summary

J-06 ("Restarts stop hurting — the durable setups scan cache"), the seventh and final Must-have
journey of "The Fast Wall" interlude, landed cleanly: `compute_setups` gained a durable, restart-
surviving SQLite tier keyed on config CONTENT (not the fragile `id(config)`), byte-identically. With
J-01–J-05 and J-07 already `passing` and re-verified this iteration, **all 7 Must-have journeys are
now `passing`** with positive, personally-opened evidence; scan is CLEAN, coherence is COHERENCE-PASS,
no anti-goal is violated, and no goal-edit drift exists. Per the decision tree (rule 3) this is
GOAL_ACHIEVED — the first key; the outer loop's deterministic gates + fresh-context confirm are the
second.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | `reports/phase-goal-fast_wall-iter-6-ui-test-results.md` (UT-J-01 PASS: backend log shows zero `POST .../compute` before/during the GETs) + `reports/qa/goal-fast_wall-iter-6-evidence/UT-03-edge-report-not-computed.png` (not-computed panel frozen text) |
| J-02 | passing | passing | Keyless/automated per goal.md; owned files (`bars.py`/`datasets.py`/`dataset_index.py`) git-confirmed zero-diff; full suite 1544 green incl. `test_dataset_index.py`; supplementary `reports/qa/goal-fast_wall-iter-6-evidence/UT-J-02-J-03-tradability-path.png` |
| J-03 | passing | passing | Keyless/automated per goal.md; owned files (`levels.py`/`tradability.py`/`backtests.py`) git-confirmed zero-diff; full suite green incl. source-introspection guards `test_backtests.py:1500-1508`/`:932-943` |
| J-04 | passing | passing | `reports/phase-goal-fast_wall-iter-6-ui-test-results.md` (UT-J-04 PASS: `POST compute` → poll → `GET edge-report` on done → terminal frozen "No edge-report cells yet.") + `reports/qa/goal-fast_wall-iter-6-evidence/UT-J-04-after-fullpage.png` |
| J-05 | passing | passing | Keyless-on-fixtures per goal.md; `edge_report_backtest_cache.py`/`edge_report.py` bodies git-confirmed zero-diff (only the reused `_config_content_hash` import); full suite green incl. `test_edge_report_backtest_cache.py`; the UT-J-04 compute click exercised the `run_pair`/durable-sub-cache path end-to-end |
| **J-06** | **failing** | **passing** | 8 non-vacuous keyless TCs read in full in `iter-6/iter-diff.md` (TC-6 mutation probe pre-seeds a deliberately-wrong payload → returned verbatim, proving the durable-hit branch is genuinely read; TC-1/TC-5 byte-identity; TC-3 content-hash-not-fingerprint); audit independently re-ran TC-1/TC-3/TC-6 green; full suite 1544 pass; browser `UT-01-ready-state-fullpage.png` + `UT-02-before-filter.png` (every section ready/honest-empty, zero loading panels); dev's real durable-cache-on-disk confirmation (`setups_scan_cache.db` written with one real row) |
| J-07 | passing | passing | `reports/phase-goal-fast_wall-iter-6-ui-test-results.md` (UT-J-07 replay PASS) + `reports/qa/goal-fast_wall-iter-6-evidence/J-07-verify.png` (on-page fingerprint `4d665603569b9dbf`, frozen register "simulated — assumed fees/slippage — not indicative of live results", honest "insufficient sample (n < 5)") |

## Anti-goal Check

Worked from `iter-6/scan-report.md` (CLEAN) + `iter-6/iter-diff.md` (7 files, all on-scope) +
`iter-6/coherence.md` (COHERENCE-PASS).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials | OK | scan-report CLEAN; only a new env-var NAME (`TAPEOLOGY_SETUPS_CACHE_DB`) referenced in code, no secret value; no new config/env file |
| Paid/external SaaS | OK | scan-report CLEAN dependency findings; no manifest diff — new module uses only stdlib `sqlite3`/`hashlib`/`json`/`os` |
| License changes | OK | scan-report CLEAN; no LICENSE/license-field diff |
| Fabricated/substituted data | OK | TC-6 mutation probe proves the durable-hit path is genuinely read (not a silent fresh rescan); TC-5 delete-DB → byte-identical recompute; coherence confirms no second computer, no divergent hash |
| Rail 3 — Frozen foundations | OK | `config_fingerprint` `4d665603569b9dbf` (QA + review + audit re-computed + on-page J-07 screenshot); all frozen files (`levels`/`tradability`/`backtests`/`bars`/`datasets`/`dataset_index`/`edge_report*`/`config`/`mcp`/frontend) git-confirmed zero-diff |
| Interlude — No source-guard weakening | OK | both source-introspection guards (`test_setups.py:758-771`, `:995-1017`) pass byte-unmodified — independently git-confirmed (diff is a pure append after line 1072) + QA + review + audit re-ran green; MCP 18-tool count guard unchanged |
| Interlude — No divergent accelerator output | OK | TC-1/TC-5 `json.dumps(sort_keys=True)` byte-identity; stored WITHOUT `sort_keys`; audit traced the JSON round-trip faithful; equivalence/determinism tests present and non-vacuous |
| Interlude — Accelerators are never sources of truth | OK | TC-5 deleting the DB loses nothing (one byte-identical recompute); coherence grep confirms no route/MCP/UI reads `setups_scan_cache.db` directly — only `compute_setups`'s internals |
| Interlude — No compute on page load (operator-run only) | OK | audit B1 independently confirmed this rail is scoped to the backtest SWEEP; the setups scan is a different, lighter read-path compute that has always run on `GET /research/setups` and is only accelerated here; the GET/compute path is zero-diff this iteration |
| Interlude — Verification trust boundary never weakens | OK | `bars.py`/`datasets.py` load paths zero-diff; scan-cache key includes `_store_signature` (per-series checksums) so any content change busts both tiers; a miss re-verifies via `_run_full_panel_scan` |
| Rail 8 — Read-only MCP | OK | MCP tool count still 18 (QA + review + audit); no MCP surface change |
| Rail 6 — Single source of truth | OK | coherence COHERENCE-PASS: same sole computer (`_run_full_panel_scan`), same two endpoints, same served shape `{"events": [...]}` |
| Rails 1,2,4,5,7,9,10 / gate-register-vocab / enhancement-loop-box | OK | full suite green incl. `test_no_execution_path.py`; no PnL/gate/label/register change; no goal.md edit (J-06 is human-authored, not proposer-appended) |

## Next-Step Recommendation

Halt — GOAL_ACHIEVED. All 7 Must-have journeys of "The Fast Wall" interlude are `passing`. The
interlude's deliverables are complete: `/structure` never computes on load (J-01), the stores stop
re-reading with durable caches + dataset index (J-02), the arm memo collapses per-tick recomputes
(J-03), the operator-run compute (button + background job + CLI warmer) works (J-04), the sweep is
resumable + parallel (J-05), the setups scan cache survives restarts (J-06), and the era-1–5B
foundation is byte-identical (J-07, fingerprint frozen).

One cosmetic non-blocker for whenever `test_setups.py` is next edited for a substantive reason (do NOT
reopen this iteration for it): the stale `id(config)` docstring aside at `test_setups.py:1027` (flagged
MINOR by review, OBSERVATION by audit, already deferred by both). It affects no journey and no
anti-goal. The operator-only real-corpus "restart → `/structure` ready within 10s" figure remains
tagged `*(operator-verified on the real corpus)*` in goal.md — gather as bonus evidence if/when a
credentialed real-corpus run happens; correctly excluded from this iteration's Definition of Done.

## Halt Justification

GOAL_ACHIEVED via decision-tree rule 3, all preconditions met:
1. **Every Must-have journey is `passing`** (J-01–J-07), each with positive, personally-verified
   evidence — no journey is `failing` or `unknown`. J-06 (the sole status change) is proven by 8
   non-vacuous keyless test cases (audit independently re-ran the crux TC-1/TC-3/TC-6), a green
   1544-test suite, real browser screenshots of the honest-empty no-regression `/structure` state, and
   a real on-disk `setups_scan_cache.db` row written through a live page load.
2. **No unresolved anti-goal violation** — every category answered explicitly above; scan CLEAN,
   the two critical source-introspection guards + the fingerprint + the MCP count all byte-unmodified,
   the "No compute on page load" rail confirmed correctly scoped (audit B1).
3. **coherence.md is COHERENCE-PASS**, not COHERENCE-FAIL — no structural veto (no duplicate computer,
   no divergent hash, no scattered surface; the diff adds one pure-storage accelerator with a single
   canonical owner).
4. **No goal-edit drift** — no `journeys-changed.md`; all 7 recorded `spec_hash` values equal the
   current `goal.md` hashes, so no prior pass was earned on stale text.

This is the first of the two-key confirm; the outer loop re-verifies with deterministic gates and a
fresh-context second key.
