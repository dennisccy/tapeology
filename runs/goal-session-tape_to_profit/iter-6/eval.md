# Iteration 6 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-06 (versioned indicator profiles) is newly passing on cross-checked multi-surface evidence: `GET /research/profiles` lists `default` plus the additive candidate `candidate-faster-warmup`, the fixture backtests run to `done` under both profiles with the `default` fingerprint pinned unchanged at `4d665603569b9dbf` and the candidate distinct at `8c2c0fbf978228e3`, and an unknown profile returns an honest `422`. No journey regressed, no anti-goal was violated, and coherence is PASS. Seven of eight Must-have journeys now pass; only J-07 (the candidate sweep / promotion-gate harness) remains, so the goal is not yet achieved.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | reports/qa/goal-tape_to_profit-iter-6-evidence/J-01-verify.png (golden replay; `/journal/[id]` honest not-found, 4-link nav) |
| J-02 | passing | passing | reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-02-result.png (record 200 + checksum, 409 re-tag, ambient-check no rows) |
| J-03 | passing | passing | reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-03-result.png (suite; results-table row) |
| J-04 | passing | passing | reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-04-result.png (founding row, fingerprint `4d665603569b9dbf`, row_count 1) |
| J-05 | passing | passing | reports/qa/goal-tape_to_profit-iter-6-evidence/J-05-verify.png (golden replay; 4-link nav incl. Performance) |
| **J-06** | **failing** | **passing** | **reports/qa/goal-tape_to_profit-iter-6-evidence/UT-J-06-result.png (both profiles, champion v1/default, default fp `4d665603569b9dbf`)** |
| J-07 | failing | failing (not targeted; carried over) | reports/phase-goal-tape_to_profit-iter-0-ui-test-results.md (feature absent — out of scope this iter) |
| J-08 | passing | passing | reports/qa/goal-tape_to_profit-iter-6-evidence/J-08-verify.png (golden replay; Studies surface intact) |

Deterministic gates: scan-report.md CLEAN; review PASS_WITH_NOTES (one MINOR test-completeness nit, not a fail — no fail-open); browser QA PASS 7/7; coherence.md COHERENCE-PASS. Full backend suite 1004 passed / 1 skipped (≥ iter-5's 988 baseline, +16 net-new, none deleted), observer-equivalence 7/7, `test_no_execution_path.py` 4/4.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No live execution path (critical) | OK | scan CLEAN; `test_no_execution_path.py` 4/4 green; J-03 grep found no broker/order/paper-trading code; no execution modules in the diff |
| No profit claims / no advice (critical) | OK | register string "simulated — assumed fees/slippage — not indicative of live results" present on default_run (UT-J-06) and the ledger founding row (UT-J-04); candidate's negative hold-out net R (-0.1728) framed as a measured difference, not a claim |
| Default engine outputs frozen (critical) | OK | `default` fingerprint `4d665603569b9dbf` unchanged — pinned test + cross-confirmed in both UT-J-06 (default_run) and UT-J-04 (founding-ledger provenance); `resolved_for_profile(default) is CONFIG` (identity); candidate overlay via `dataclasses.replace`, shared singleton never mutated; observer-equivalence 7/7 |
| No train-only promotion (critical) | OK | No promotion this iter (out of scope); champion still `v1/default` (UT-J-06); PnL ledger row_count still 1 (UT-J-04) |
| No ML / no online tuning | OK | candidate is a single config-enumerated threshold (`warmup_min_events` 40→30); no fitted models, no optimizer |
| No fabricated data — honest failure states (critical) | OK | unknown profile → honest `422` listing `['default','candidate-faster-warmup']`; no synthesized data; scan CLEAN |
| Single source of truth (critical) | OK | coherence.md: ONE registry `Config.profile_definition` feeds both `GET /research/profiles` and the backtest route; ONE `config_fingerprint()` hasher; no second computation path |
| MCP is read-only (critical) | OK | `app/mcp/` zero-diff (coherence + dev handoff); profiles reach MCP via existing `get_endpoint` allowlist |
| Persistence stays scoped (critical) | OK | no new persistence; ledger untouched (row_count 1); J-02 ambient-check: watch/unwatch wrote no dataset rows |
| Enhancement loop stays in its box (critical) | OK | `docs/goal.md` untouched (human-authored J-06 work; proposer did not run) |
| Secrets / paid SaaS / license | OK | scan-report.md CLEAN — no secret, dependency, or license findings on added lines; no manifest changes in the diff |

## Next-Step Recommendation

Target **J-07** (the candidate sweep harness `python -m app.research.pnl_scan --out <path>`) — the last remaining Must-have journey, head-and-only of the J-06 → J-07 chain now that J-06's candidate registry exists. Recommend running it at **full** depth (see Halt Justification for why this one warrants the full pipeline). Build in from the start, per accumulated lessons:

- **Control minimum-n both ways (lesson iter-4).** The committed fixture pair arms only n=1 per split, below the configured `pnl_min_sample_size` (5). On the fixtures the sweep MUST honestly report **zero survivors** (n < 5) and **exit 0**, with the champion pointer NOT moved and NO PnL-ledger row appended. A separate scenario with n ≥ the minimum is needed to exercise the actual survivor/promotion path — do not weaken the min-n gate to force a green.
- **The J-06 candidate is not a survivor.** `candidate-faster-warmup`'s hold-out net R is -0.1728 vs default +0.3334 — it fails the "net R AND net $ on hold-out" gate, so the sweep must label it rejected/overfit, never promote it. This is the honest-negative path the report must show.
- **Promotion mechanics carry the critical anti-goals.** When a survivor does exist: append exactly ONE append-only PnL-ledger row (J-04 discipline, provenance-stamped) and move the champion pointer **without mutating the `default` profile or any engine default** (J-06/J-08 byte-identity must survive). Report per candidate: train + hold-out net R/$ deltas, n per split, per-dataset breakdown, `survivor`, and `robustness: robust|speculative`. Deterministic under fixed seeds (identical re-runs → identical reports).
- Keep J-01–J-06 and J-08 in the required-still-passing set; J-01/J-05/J-08 via golden replay, J-02/J-03/J-04/J-06 via the backend suite + in-page fetch.

## Halt Justification

Not halting — verdict is CONTINUE. Progress was made (J-06 failing → passing) and one tractable journey remains (J-07).

## Depth Rationale (full for J-07)

Six iterations shipped lean, including this one's risky engine/config seam — so this is not reflexive escalation but targeted rigor for the single riskiest, goal-closing journey. J-07 is the **only** journey that performs an anti-goal-gated state mutation: promotion moves the champion pointer AND appends to the PnL ledger, gated entirely by the critical **"No train-only promotion"** anti-goal (hold-out survival on net R AND net $ with minimum n). A defect there is a *critical anti-goal violation*, not a missing feature — a far larger blast radius than the read-only additive work of J-01–J-06. J-07 is also the goal-closing journey: a passing J-07 makes the next evaluation a GOAL_ACHIEVED candidate, so the full pipeline's independent auditor + QA verdict on exactly the promotion/champion-movement/ledger-append mechanics is proportionate insurance before the two-key GOAL_ACHIEVED confirm. This is a recommendation, not a forcing ESCALATE — iter-6 itself surfaced no ambiguity (clean verify-and-complete), so the decision tree yields CONTINUE; the depth call is forward-looking risk budgeting.
