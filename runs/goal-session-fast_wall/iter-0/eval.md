# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Honest baseline established for the "Fast Wall" interlude with **zero source diff** (verify-only,
`git diff --stat -- apps/` empty; `iter-diff.md` = "no changes"; scan-report CLEAN). Six target
journeys (J-01–J-06) are **failing** exactly as the spec predicted — every one of the interlude's
new modules/functions is confirmed absent by independent grep + the zero-diff scan — and J-07 (the
foundation regression sentinel) is **passing** on strong evidence (full suite 1392 passed / 7
skipped / 0 failed, `config_fingerprint` 4d665603569b9dbf, equivalence 22/22, four verified
screenshots). No anti-goal violation and no regression (there is no prior pass to regress — first
session iteration). Next target is J-01 ("stop the bleeding"), the smallest self-contained fix that
also removes the live browser-QA CPU hazard documented below.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Stop the bleeding (GET never computes) | none (new) | failing (expected) | `routes.py:2110-2115` calls `run_strategy_comparison_report` unconditionally; `edge_report_cache.py` has only `get_or_compute` (no `lookup`/`compute_and_publish`); no `peek_strategy_comparison_report`; no not-computed panel in `structure/page.tsx` — all grep-confirmed + zero-diff scan. `ui-test-results.md` UT-J-01 |
| J-02 Stores stop re-reading | none (new) | failing (expected) | No stat-keyed cache in `bars.py`/`datasets.py`; no `dataset_index.py`. Live `GET /research/datasets` = **30.13s / 8,588 B / 18 datasets** (goal.md cites 31.4s). `reports/qa/goal-fast_wall-iter-0-evidence/J-02-datasets-latency.txt` |
| J-03 The arm memo | none (new) | failing (expected) | No `level_change_points` / `basis_day_key` / `_StructureArmMemo` in `levels.py`/`tradability.py`/`backtests.py` (grep no-match). `ui-test-results.md` UT-J-03 |
| J-04 Operator-run compute | none (new) | failing (expected) | No `edge_report_compute.py`; `GET`/`POST /research/edge-report/compute` → 404; no "Compute edge report" text in `structure/page.tsx`. `ui-test-results.md` UT-J-04 |
| J-05 Resumable + parallel sweep | none (new) | failing (expected) | No `EdgeReportBacktestCache`, no `run_pair` seam in `edge_report.py` (grep no-match). `ui-test-results.md` UT-J-05 |
| J-06 Durable setups scan cache | none (new) | failing (expected) | No `setups_scan_cache.py`; `setups.py:403` key still `(id(config), _store_signature(store))` (restart-wiped `_SCAN_CACHE`). Live `GET /research/setups` = **268.95s (4m29s)** cold. `reports/qa/goal-fast_wall-iter-0-evidence/J-06-setups-latency.txt` |
| J-07 Foundation unchanged (sentinel) | none (new) | passing | Suite 1392 passed / 7 skipped / 0 failed; equivalence 22/22; `config_fingerprint` 4d665603569b9dbf (live call + on-page); champion v1/default unchanged; nav = 6 frozen entries. Screenshots (personally opened): `J-07-cockpit-sim-buyer.png` (Buyer Control, conf 0.932, `scenario: buyer_control`, event-log settle), `J-07-cockpit-sim-seller.png` (Seller Control, conf 0.934, `scenario: seller_control`), `J-07-performance.png` (frozen register "simulated — assumed fees/slippage — not indicative of live results"), `J-07-journal-detail.png` (on-page fingerprint 4d665603569b9dbf, "Descriptive only — not trading advice") |

**J-07 honest coverage gap (not a fail):** `/structure`'s era-5/5B interactive spot-check was NOT
live-loaded this iteration. Loading `/structure` fires a mount-time `GET /research/edge-report`
(`structure/page.tsx:1228-1255`) which, on the default real-corpus backend with a cold cache,
synchronously runs the never-completing sweep and pins the process for hours (goal.md Vision,
measured). The spec explicitly sanctions code-citation/SSR substitution at baseline and marks the
real recompute out of scope; the dev SSR-probed `/structure` (curl GET 200, all era-5/5B markers
present) and the suite covers the backend structure computations. With a zero-code diff nothing
could have regressed. J-07 is scored `passing`; the `/structure` live-interactive leg is deferred to
the first iteration that removes the hazard (J-01).

## Anti-goal Check

Zero product diff this iteration (`iter-diff.md` = "no changes"; scan-report CLEAN — no secret,
dependency, or license finding). Every category is therefore trivially clean, and the frozen-text
checks were positively confirmed in screenshots.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials committed | OK | scan-report CLEAN; zero diff; no new config/env file |
| Paid/external SaaS dependency | OK | zero diff; no manifest change; no network call made (read-only GET probes only) |
| License change | OK | scan-report CLEAN; no LICENSE diff |
| Fabricated/substituted data | OK | Latencies honestly measured on the REAL corpus (30.13s, 268.95s); no fixture placed in a prod path; `edge_report_cache.db` byte-identical before/after |
| #1 No execution path | OK | no code change; tier-1 guard in the green suite |
| #2 No profit claims / advice | OK | Performance register banner + cockpit "Descriptive only — not trading advice" verified intact in screenshots |
| #3 Frozen foundations | OK | `config_fingerprint` 4d665603569b9dbf; equivalence 22/22; zero diff |
| #4 Hold-out-only promotion | OK | champion pointer unchanged (`v1`/`default` via `GET /research/profiles`) |
| #5 No lookahead | OK | no code change |
| #6 Single source of truth | OK | no new value introduced |
| #7 Deterministic / seeded | OK | full suite green |
| #8 Read-only MCP | OK | no MCP change; new compute routes not built (404) |
| #9 Immutable data | OK | read-only GET probes only; no dataset/bar/journal mutation |
| #10 Persistence stays scoped | OK | no recording/fetching act performed |
| Interlude: accelerators never sources of truth | OK (N/A) | no accelerator built this iteration |
| Interlude: no compute on page load | OK | the defect (compute-on-GET) is confirmed PRESENT as the baseline to fix — J-01's target; no new compute path introduced |
| Interlude: verification trust boundary | OK (N/A) | no cache/serving path changed |
| Interlude: no divergent accelerator output | OK (N/A) | no accelerator built |
| Interlude: no gate/register/vocabulary drift | OK | frozen register text verified verbatim in screenshots |
| Interlude: no source-guard weakening | OK | zero diff; guard tests green in the full suite |
| Interlude: enhancement loop stays in its box | OK (N/A) | proposer not engaged this iteration |

## Coherence

`coherence.md` is **absent** for iter-0. This is expected for a zero-diff verify-only baseline (no
new information architecture, no new data-contract value to audit). Absence is treated as NOT clean
for the `GOAL_ACHIEVED` gate — moot here, since 6/7 journeys fail and `GOAL_ACHIEVED` is not on the
table. It is NOT a `COHERENCE-FAIL`, so it does not force a consolidation pass. The next feature
iteration should produce a real coherence audit.

## Next-Step Recommendation

Build **J-01 alone** ("Stop the bleeding") next, per goal.md's dependency order (J-01 → J-02 → … )
and the priority rubric (smallest, self-contained, an unblocker):
`EdgeReportCache.lookup` + `compute_and_publish` beside the untouched `get_or_compute`; the shared
cache-DB-path resolver; `edge_report.peek_strategy_comparison_report` (cold → honest not-computed
payload, warm → verbatim report, empty registry → today's shape); rewire `GET /research/edge-report`
(preserving the `cache=cache` kwarg and the explicit 500); and the `/structure` "Edge report not
computed yet." panel leaving the frozen "No edge-report cells yet." / register texts byte-identical.
J-01 also **removes the browser-QA CPU hazard** (see below), unblocking live `/structure` checks
for every later iteration.

**Depth = full.** This is the session's first code-delivery iteration and it carries the
interlude's headline CRITICAL anti-goals directly: no-compute-on-page-load, warm-cache
byte-identity, and REST↔MCP proxy byte-identity — exactly the invariants the auditor and
ux-regression lanes exist to verify — plus a browser-verifiable frontend panel with a
frozen-text-preservation requirement. The full pipeline (audit + ux-regression + closure) is the
prudent choice for this opener; adaptive lean depth can resume once the pattern is proven.

## Halt Justification (if halting)

N/A — not halting. Verdict is CONTINUE. Blocker is ordinary tractable dev work (features not yet
built); the real corpus is present locally, so no journey is human-blocked and no credential/network
action is required.
