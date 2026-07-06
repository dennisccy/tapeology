# Iteration 2 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-02 (deterministic, lookahead-free support/resistance levels) was built end to end and is genuinely passing: `GET /research/levels` + the read-only MCP `levels` tool serve one canonical `compute_levels` output, lookahead-free by construction (bars filtered `ts <= as_of` before any detector), byte-identical, and config-owned. I independently reran the J-02 acceptance suite plus the J-07 equivalence/fingerprint sentinel (exit 0, 48 tests) — the reports are corroborated, not merely trusted. Coherence is COHERENCE-PASS and the diff scan is CLEAN; no anti-goal violated; J-01/J-07 intact. J-03–J-06 remain failing exactly as scoped.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 (multi-timeframe bar store) | passing | passing | Required-still-passing. Full backend suite green this iter (QA: 1095 passed incl. `test_bars.py`/`test_bars_api.py`); guarded by the fingerprint + equivalence I reran (exit 0). |
| J-02 (deterministic S/R levels) | failing | **passing** | Backend/machine-surface journey — no browser step (browser QA correctly SKIPPED). QA test-plan TC-01..TC-18 all PASS (`reports/qa/…-iter-2-qa.md`); I independently reran `tests/test_levels.py`+`test_levels_api.py`+2 MCP tests+equivalence → exit 0 (48 passed); audit PASS_WITH_GAPS traced the lookahead-free choke point and confirmed the physical-truncation proof is non-vacuous. |
| J-03 (confluence A/B/C classes) | failing | failing | Out of scope. `GET /research/levels` ships levels only; `classes` field deliberately absent (dev handoff + audit §Domain); no clustering/scoring code. |
| J-04 (structure_tape strategy) | failing | failing | Out of scope. `grep -rn "structure_tape\|/research/strategies" apps/backend/app/` → no matches; `/research/strategies` still 404s. |
| J-05 (class-scaled stop/reward/size) | failing | failing | Out of scope. No strategy registry / backtest / sizing machinery (transitively absent — no `structure_tape`). |
| J-06 (honest v1-champion comparison) | failing | failing | Out of scope. No named-strategy edge-report/sweep path added. |
| J-07 (archived-eras regression sentinel) | already_passing | already_passing | `Config().config_fingerprint()=='4d665603569b9dbf'` re-verified live; `test_observer_equivalence.py`+`test_profile_equivalence.py` green (exit 0); `git diff 37d3ad2..HEAD -- apps/frontend/` empty. |

Status change this iter: **J-02 failing → passing** (the only delta). No regressions.

## Anti-goal Check

Worked from `iter-2/scan-report.md` (CLEAN — no secret/dependency/license finding) + `iter-2/iter-diff.md` (read `levels.py`, the config/routes/mcp hunks, both test files) + my own greps.

| Anti-goal (critical unless noted) | Status | Notes |
|-----------|--------|-------|
| No live execution path | OK | `levels.py` is pure computation over stored bars; one GET route; one read-only GET MCP proxy. No broker/order/fill/position code (that is J-04/J-05, unbuilt — grep-confirmed). |
| No profit claims / no advice | OK | J-02 adds no $/PnL/advice. Levels carry price/timeframe/type/touch_count/strength — structural facts only. |
| Tape engine / `default` / `v1` frozen | OK | Fingerprint pinned `4d665603569b9dbf` (verified live); observer+profile equivalence green (exit 0); engine/serializers diff empty (audit-confirmed). 3 new `sr_*` fields correctly in fingerprint `excluded` set. |
| No train-only promotion | OK | No strategy/backtest/champion/promotion code added (grep-confirmed). |
| No lookahead | OK | `_bars_as_of` filters `ts <= as_of` before every detector; prior-period gate `bar.epoch+period > as_of` skips the forming period; swing pivots need N confirming bars each side. Physical-truncation proof (`test_lookahead_free_…`) asserts truncation dropped bars AND byte-identity — reran green. |
| No ML / no online tuning | OK | Pure deterministic functions; params config-enumerated; no fitting/optimizer. |
| No fabricated data — honest failure states | OK | Three distinct honest states (`no_bar_series_for_symbol` true / empty-with-flag-false / 422 matrix). Documented gap B1 (corrupt *sole* series aliases to `no_bar_series_for_symbol:true`) is honest-empty, not fabricated — no invented data, no error masked as fake-success; out of J-02's scoped states. Minor, carry to J-03. |
| Single source of truth | OK | `compute_levels` is the sole computer (coherence: only definition + only call site); route serves verbatim; MCP byte-identity test green. No second computation path. |
| No capital/portfolio management | OK | No account/equity/position tracking (J-05, unbuilt). |
| MCP read-only | OK | `levels` is a GET proxy; only verb issued is GET; args validated before any HTTP call; no mutating tool. |
| Persistence stays scoped | OK | `levels.py` owns no persistence; reads via `BarStore`; no ambient recording, no new writes. |
| Enhancement loop inside its box | OK — N/A | J-02 is a human-authored journey; no proposer edit to `docs/goal.md` this iter. |
| Secrets (scan) | OK | Scan CLEAN. README changed the Alpaca env-var *name* `ALPACA_SECRET_KEY`→`ALPACA_API_SECRET` (doc correction), no secret value committed. |

No violation, critical or minor. Coherence: **COHERENCE-PASS** (no structural veto).

## Next-Step Recommendation

Advance to **J-03 — confluence zones and A/B/C conviction classes** (the natural dependency successor; it clusters the J-02 levels this iteration produced). It delivers the *classes half* of Data-Contract Row 39 via an additive `classes` field on the existing `GET /research/levels` + MCP `levels` — no new endpoint/owner. Depth **full**, by the same three triggers that justified J-02: (a) a new canonical computation (confluence scoring + A/B/C grading); (b) new correctness tests beyond browser smoke (deterministic clustering, byte-identical re-runs, config-owned tolerance/class thresholds, honest class labelling); (c) it extends the critical **no-lookahead** property to classes — and, being a machine surface, the tests ARE the acceptance (no browser smoke to catch a wiring slip), which warrants the fuller audit. Carry forward: the audit's B1 seam — J-03, when it consumes levels, must decide whether a corrupt *sole* series needs a distinct honest state vs an absent one.

## Halt Justification (if halting)

N/A — not halting. Progress made (J-02 newly passing); Must-have journeys J-03–J-06 remain and are fully tractable keyless; no regression, no critical anti-goal violation, coherence PASS. Decision tree lands on CONTINUE (rules 1–4 skipped: no regression, no human-owned blocker, not all journeys passing, no fail-open/ambiguity).
