# Iteration 5 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

A backend-only enabler pass that resolves the two blocking watch-items the iter-4 evaluator named as owned by J-05 — audit **B1** (recency-boundary honesty) and audit **B3** (a shared, bounded scan cache) — with **zero journey flips by design** (J-05 stays `failing` until iter-6 renders its UI). Both changes live entirely inside `apps/backend/app/research/setups.py`; I independently confirmed the product diff is exactly `setups.py` + its two test files (every frozen file absent), `config_fingerprint == 4d665603569b9dbf`, and that the pinned AAPL 2026-06-22 setups event stays byte-identical (`rejected`, boundary flag `false`, effective horizon 78) — so J-02 (owns the registry) and J-04 (edge report reads `compute_setups`) do not regress. Forward progress on J-05's substrate; coherence `COHERENCE-PASS`; no anti-goal violation.

## Journey Results This Iteration

No status changed this iteration (backend-only enabler; no journey was a flip target). J-01/J-02/J-04/J-07 re-verified green; J-03 keyless substrate re-verified unbroken; J-05/J-06 carried failing.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The tradable level map | passing | passing | `tradability.py` absent from `git diff --name-only 832ea80b -- apps/`; `config_fingerprint 4d665603569b9dbf` recomputed by evaluator |
| J-02 The wide scan / case registry | passing | passing | `setups.py` changed **additively** only; pinned AAPL 2026-06-22 byte-identical (`test_aapl_pinned_2026_06_22_event_is_rejected_with_negative_forward_returns` — evaluator re-ran, 8 passed); `test_setups.py`+`test_setups_api.py` green |
| J-03 Real tape at the wall (credentialed) | partial | partial | keyless enrichment unbroken after B3: `test_enriched_detail_read_never_leaks_into_the_shared_cached_list` (real J-03 PG fixture, non-empty `tape_timeline`) green; credentialed ≥10-window headline still not durably established (operator-gated) |
| J-04 The edge report | passing | passing | `edge_report.py` absent from diff; reads cached `compute_setups` byte-identically — `test_cache_hit_is_byte_identical_to_a_fresh_uncached_scan` + `test_edge_report.py`/`test_edge_report_api.py` green (evaluator re-ran) |
| J-05 /structure decluttered | failing | failing (by design) | Its two named blockers **B1+B3 resolved** this iter (forward progress); no `/structure` UI built (frontend diff empty) — deferred to iter-6 |
| J-06 Cockpit confluence | failing | failing | Untouched (frontend diff empty); deferred to iter-7 |
| J-07 Foundation sentinel | already_passing | already_passing | All frozen files absent from diff; `config_fingerprint 4d665603569b9dbf`; `test_strategies_api.py` green (registry frozen) |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No execution path, ever | OK | Diff adds only two derived setups fields + an in-memory cache; no brokerage/order/trade path; scan-report CLEAN |
| No profit claims / no advice | OK | No UI copy, no new `$` figures; new fields are `effective_reaction_horizon_bars` (int) + `reaction_boundary_truncated` (bool); `edge_report.py` untouched |
| Frozen foundations (v1/default/engine/levels/BarStore byte-identical) | OK | `config_fingerprint 4d665603569b9dbf` recomputed; all frozen files absent from `git diff --name-only 832ea80b -- apps/`; `compute_setups` signature unchanged, scan body byte-identical (`_run_full_panel_scan`), non-boundary events byte-identical (pinned AAPL test green) |
| Hold-out-only promotion | OK | No champion change; `backtests.py`/`config.py`/`strategies.py` absent from diff; registry order frozen |
| No lookahead | OK | B1 *discloses* the recency boundary (store lacks forward bars) — opposite of lookahead; reaction reads only existing bars (`min(touch+horizon, len-1)`); as-of scan logic unchanged |
| Single source of truth | OK | coherence `COHERENCE-PASS`; B3 cache is a rebuildable accelerator of the one `compute_setups` owner (byte-identical), not a second source; two fields are additive attributes on the existing setups value, registered in blueprint.md |
| Deterministic and seeded | OK | Cache byte-identity + determinism + computed-once + checksum-bust tests green; keyed on store-content signature + config identity; no wall-clock/unseeded randomness added |
| Read-only MCP | OK | `routes.py` absent from diff; no new MCP tool |
| Immutable data | OK | `datasets.py` absent; cache is in-memory, never persisted, never re-tags datasets; immutable-safety test proves enriched read never leaks into shared list |
| Persistence stays scoped | OK | No recording change; B3 cache is process-local memory, never disk-persisted |
| Era-5B: tradable map is a lens, not a 2nd levels engine | OK | `tradability.py`/`levels.py` absent from diff |
| Era-5B: morning-markup discipline | OK | B1 concerns forward-reaction horizon (post-touch), not map basis; as-of discipline unchanged |
| Era-5B: descriptive, never imperative | OK | No UI copy this iter; new fields numeric/boolean |
| Era-5B: recording explicit/windowed/logged | OK | No recording change |
| Era-5B: feed honesty — never pool | OK | No analysis/feed change; `edge_report.py` (feed cell dimension) absent from diff |
| Era-5B: no gate bending for a headline | OK | n≥5/`insufficient_sample` logic unchanged (`edge_report.py` absent) |
| Era-5B: keys never committed/logged | OK | scan-report CLEAN; evaluator grep of the 3 changed files for `APCA/ALPACA/AKIA/BEGIN` → no matches |
| Era-5B: live mode untouched | OK | No frontend/cockpit change |
| Era-5B: no vocabulary drift | OK | No "paper/shadow trading", "annualized", "expected profit"; field names are technical/descriptive |
| Fabricated/substituted data | OK | `SYN-SETUPS-BOUNDARY` is a synthetic **test** fixture (in `tests/`, feed-stamped `sip`) exercising the boundary path only; real path uses the operator's real store (13/801 real events flagged) — no fabrication in a production path |
| Secrets / paid SaaS / license | OK | scan-report.md CLEAN — no secret, dependency, or license finding on added lines; no manifest change in the diff |

## Next-Step Recommendation

Build **J-05** at depth **full** — the pure-frontend `/structure` render on this now-recency-honest, now-bounded substrate: Tradable Map as default (`GET /research/tradability`) with the raw-levels view behind an explicit toggle, the Case Studies browser + per-event drill-in (`GET /research/setups` + `/setups/{id}`, rendering boundary events honestly via the new `reaction_boundary_truncated`/`effective_reaction_horizon_bars` fields), and the Edge Report section (`GET /research/edge-report`) — every value read verbatim (zero client recomputation), era-5 fetch control + provenance badge preserved. Full depth is warranted: browser-verifiable, coherence-relevant (new UI surfaces → nav / duplicate-home / parallel-shell checks), and a zero-recomputation read across three endpoints. **Carry-forward watch-item (non-blocking):** iter-6's browser page-load may fire the setups list and edge-report concurrently against a cold B3 cache; the review/audit/coherence-flagged non-atomic two-key cache write (`setups.py:377-378`) has a narrow torn-read window (new key paired with a `None` cold result → a possible 500) — a one-line atomic tuple rebind or `threading.Lock` closes it (hardening, not a correctness prerequisite for a single operator). Parallel operator-gated carries (do NOT block J-05): complete J-03's credentialed ≥10-window headline + pinned-AAPL 06-22 drill-in; J-06 cockpit band overlay + chip stays queued for iter-7.

## Halt Justification (if halting)

N/A — not halting. Not GOAL_ACHIEVED (J-03 `partial`, J-05/J-06 `failing`); not REGRESSION (no journey moved passing→failing — J-02/J-04, the real regression surfaces downstream of the modified `setups.py`, re-verified byte-identical by the evaluator; no critical anti-goal); not STALLED (iter-6's pure-frontend J-05 render is abundant, agent-buildable, browser-verifiable work on a now-proven-stable substrate); not ESCALATE (already full depth, all lanes pass-class — review PASS_WITH_NOTES, QA PASS, audit PASS_WITH_GAPS with only non-blocking concurrency observations, coherence COHERENCE-PASS; no fail-open, no cross-cutting ambiguity, and J-05 was a planned dependency-ordered build, not a repeatedly-failing flip target).
