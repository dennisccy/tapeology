# Iteration 3 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-03 (confluence zones + A/B/C conviction classes) moved failing → passing: `GET /research/levels`
and the byte-identical MCP `levels` proxy now serve confluence zones (member levels + timeframes, a
timeframe-weighted score, an honest A/B/C class) as an additive field on the existing `compute_levels`
owner — no new module, endpoint, or MCP tool. It is a machine surface (browser QA correctly SKIPPED),
so the test suite is the acceptance: QA and the audit independently re-ran it (1107 passed / 1 skipped
/ 0 failed; 114 targeted passed), and I personally re-verified the J-07 sentinel, frozen frontend, and
no scope creep. Required-still-passing J-01/J-02/J-07 stay green; J-04/J-05/J-06 remain failing and
out of scope. Not GOAL_ACHIEVED — three Must-have journeys are still unbuilt.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | Required-still-passing; full backend suite green (QA `reports/qa/goal-tape_to_profit_support_resistence-iter-3-qa.md`: 1107 passed incl. `test_bars*`) + evaluator-reran fingerprint `4d665603569b9dbf` |
| J-02 | passing | passing | Required-still-passing; `test_levels.py`/`test_levels_api.py` green in full suite; single-source S/R unchanged (route still spreads `**result`) |
| J-03 | failing | **passing** | Machine surface (no screenshot; browser QA SKIPPED, correct). QA 14/14 TC PASS + `test_levels.py` acceptance suite (clustering/scoring/A-B-C grading/anchor-fixed/no-lookahead/honest-empty) + `test_mcp_server.py` byte-identity, all independently re-run by QA (`...-iter-3-qa.md`) and audit (`docs/handoffs/...-iter-3-audit.md`, exit 0) |
| J-04 | failing | failing | Out of scope; evaluator grep `structure_tape\|research/strategies\|class_scaled` in `apps/backend/app/` → NO MATCHES |
| J-05 | failing | failing | Out of scope; transitively absent (depends on unbuilt `structure_tape` registry) |
| J-06 | failing | failing | Out of scope; `pnl_scan`/`edge_report` remain champion-only, no named-strategy path |
| J-07 | already_passing | already_passing | Regression sentinel; evaluator-verified `Config().config_fingerprint()=='4d665603569b9dbf'` (3 new `sr_confluence_*` fields correctly excluded) + observer/profile equivalence 57 tests green + `git status apps/frontend/` empty |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials | OK | scan-report.md CLEAN; config.py added 3 numeric fields only, no env/secret files |
| Paid/external SaaS | OK | scan-report CLEAN; no manifest (requirements/pyproject/package.json) change in the diff |
| License changes | OK | scan-report CLEAN; no LICENSE diff |
| No live execution path | OK | grep NO MATCHES for `structure_tape`/broker/order code; J-04–J-06 unbuilt |
| No profit claims / advice | OK | confluence zones are structural only; no PnL/advice text added this iter |
| Frozen tape engine / `default` / `v1` | OK | fingerprint `4d665603569b9dbf` unmoved (evaluator-verified); observer+profile equivalence 57 green |
| No train-only promotion | OK | no promotion/champion change (J-06 unbuilt) |
| No lookahead (critical for J-03) | OK | `compute_confluence_zones` is a pure fn of the already-truncated `levels`; physical-truncation test asserts byte-identical zones/class at as-of T + non-vacuous "later bar absent" assertion (audit-verified vs running code) |
| No ML / online tuning | OK | deterministic anchor-fixed clustering + breadth-based grading; all thresholds config-owned; no fitting |
| No fabricated data — honest states | OK | 3 distinct honest empty states assert `confluence_zones: []`; PG fixture honestly never grades A (documented) |
| Single source of truth | OK | computed once in `research/levels.py`; MCP byte-identical to REST; coherence grep found zero second-path hits in analytics/pnl_scan/edge_report/frontend |
| No capital / portfolio mgmt | OK | no sizing/position code this iter (J-05 unbuilt) |
| MCP read-only | OK | `mcp/__init__.py` description text only; no handler/dispatch change; still byte-for-byte proxy |
| Persistence stays scoped | OK | pure derived computation over existing bar store; no new persistence |
| Enhancement loop in its box | OK | J-03 is a human-authored journey; no goal.md edit |

## Next-Step Recommendation

Advance to **J-04** (`structure_tape` as a registered strategy) at **full** depth. J-04 introduces a
config-owned strategy registry beside the frozen `v1`, a new `GET /research/strategies` endpoint +
MCP proxy, tape-confirmed structure entries (arming where a classified level's proximity band meets a
confirming tape state — rejection→fade / breakthrough→follow), and a backtest run under the new
strategy that must keep `default`/`v1` byte-identical (equivalence green, fingerprint unmoved) and
pass the critical no-broker/no-execution grep-guard. That is a new canonical computation + new
endpoint + critical anti-goal surface — squarely full-depth. It consumes exactly the A/B/C zones J-03
just shipped.

Fold in one trivial doc-parity rider (coherence WARN, non-blocking): extend the README's new
"Support/resistance level detection" capability bullet to mention confluence zones + A/B/C classes,
which currently describes only the J-02 half of the endpoint.

## Halt Justification (if halting)

N/A — not halting. Progress made (J-03 newly passing); J-04–J-06 remain tractable, keyless-on-fixtures,
and autonomously buildable in dependency order.
