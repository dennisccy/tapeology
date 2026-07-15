# goal-tradable_wall-iter-5 Audit Report

**Date:** 2026-07-15
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The two blocking watch-items the iter-4 evaluator named (audit **B1** recency-boundary honesty, audit **B3** shared scan cache) are genuinely resolved, verified by code trace rather than handoff summary. B1 is a purely additive disclosure — the `reaction`/`forward_returns` computation is byte-identical in the diff (only two derived fields added) — and its regression test exercises a real recency boundary with the shipped 78-bar horizon, not a small test-only override. B3 is a correct process-local memoization: all three call sites were traced and treat the shared cached object read-only, and the uuid-keyed store signature makes the cache both correct and free of cross-test pollution. One genuine but low-risk concurrency GAP remains (a non-atomic cache write, reviewer-flagged, self-healing on a single-operator tool); it does not compromise the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — GAP (observation, not fixed): non-atomic cache write can momentarily serve a torn key/result pair.**
`compute_setups` (`apps/backend/app/research/setups.py:373-379`) writes the cache as two separate statements:
```
_SCAN_CACHE["key"] = key      # line 377
_SCAN_CACHE["result"] = result # line 378
```
FastAPI runs sync handlers in a threadpool, so a reader entering the `if _SCAN_CACHE["key"] == key` check (line 374) in the one-statement gap between 377 and 378 could see the NEW key paired with the PREVIOUS result — on a cold process that previous result is `None`, which would surface as a 500 rather than a stale-but-valid scan. It self-heals on the next call, and the interleave requires two genuinely-concurrent `compute_setups` callers landing in a single-bytecode window after a multi-minute scan — not a realistic scenario for this explicitly single-operator, single-process, local-first tool. The dev's Known Issue #3 documents the adjacent *redundant-recompute* concurrency case but does not cover this torn-read, so the "never a torn ... result" phrasing slightly under-discloses. The reviewer independently flagged this as MINOR.
I considered rating this IMPORTANT and rejected it: the DoD's "never serves a stale result" is defined by the checksum-bust path (store mutation → re-scan), which is correct and tested; the concurrency torn-read is beyond both the DoD and the tool's realistic concurrency profile. Not fixed — fixing a GAP is scope creep. Trivial hardening for iter-6+ if desired: rebind a single tuple (`_SCAN_CACHE = (key, result)` — one name-store is atomic under the GIL) or wrap the check-write in a `threading.Lock`.

**B2 — OBSERVATION: dev Known Issue #1 ("never a wrong answer") slightly overclaims.**
The cache key uses `id(config)` (`setups.py:373`). Known Issue #1 states two distinct `Config(...)` objects are "always a safe, conservative cache miss." That misses the CPython id-reuse-after-GC case: if a config is garbage-collected and a *different-valued* config is later allocated at the same address while the store signature also matches, the cache would HIT and return the first config's result. This never bites production (all callers share the immortal `CONFIG` singleton — `routes.py:1882,1904`, `edge_report.py:447`) and effectively never bites tests (configs stay referenced for the test's duration, and every fresh store gets a unique uuid signature). Correctness impact: none observed. Noted only because the handoff's absolute "never a wrong answer" phrasing is not literally exhaustive.

### Frontend Findings

None — `Frontend Present: no`. No UI change was made or claimed. J-05's browser flip is correctly deferred to iter-6 (dev handoff Known Issue #4; `status.json` `browser_checks_run: false`). No premature journey-flip claim was found.

### Test Findings

**T1 — OBSERVATION: the pinned-AAPL non-boundary test asserts sign, not the exact forward-return magnitudes.**
`test_aapl_pinned_2026_06_22_event_is_rejected_with_negative_forward_returns` (`tests/test_setups.py:484-516`) asserts `reaction == REJECTED`, both returns non-`None` and `< 0`, exact `touch_ts`, `round_number`, and the two new boundary fields (`False`, `78`) — but not the exact `[-0.462%, -4.269%]` magnitudes the spec's DoD "asserts exact values" wording implies. In practice the byte-identity is structurally locked regardless: the diff proves the reaction/forward-return code path is untouched (only two derived fields were added — `setups.py` diff hunk at `_reaction_and_forward_returns`), and the synthetic reaction tests DO pin exact forward-return values (`tests/test_setups.py:186-189, 204-207, 226-229`). This looseness also predates iter-5 (the test existed; iter-5 only appended the two boundary-field assertions). No real risk.

**T2 — OBSERVATION: three "repeat scan determinism" tests now exercise cache-consistency, not re-scan.**
`test_repeat_scan_determinism` (`:322`), `test_aapl_repeat_scan_determinism` (`:519`), and `test_boundary_regression_is_deterministic_across_repeat_scans` (`:862`) open a second `BarStore` over the same `tmp_path` while reusing one `Config`; because the on-disk uuid series id is stable, the second call now cache-HITS (returns the identical object) rather than re-scanning. Genuine fresh-vs-cached determinism is still proven by `test_cache_hit_is_byte_identical_to_a_fresh_uncached_scan` (`:879`), which calls `_run_full_panel_scan` directly to bypass the cache. Reviewer-noted; observational only.

---

## 3. Domain Assessment

The core domain logic is correct and honest.

**B1 boundary contract.** Traced `_reaction_and_forward_returns` (`setups.py:216-266`). The boundary flag `reaction_boundary_truncated = touch_index + horizons[0] >= len(all_bars)` (`:243`) is exactly right at the equality edge: when `touch_index + horizons[0] == len(all_bars)`, the reaction close is read one bar short of the full horizon AND the horizon-0 forward return is `None` (`:258-260`), so flagging it truncated is the honest call; when `touch_index + horizons[0] == len(all_bars) - 1` the reaction reads at exactly the full horizon and the flag is correctly `False`. `effective_reaction_horizon_bars` is derived from the same `reaction_index` the reaction close already uses, so it can never disagree with the label. The design choice — *disclose* the truncation additively, never mutate the `reaction` label, never drop the event — matches the logged interpretation call and is the reversible, honest option. The regression test (`:830-859`) is the real proof the iter-2/iter-4 lessons demanded: it asserts `config.setups_forward_return_horizons_bars[0] == 78` up front, then drives a 5-bar store so the store genuinely runs out at effective-horizon 4 — a fixture that actually reaches the boundary, not one that never truncates.

**B3 single-source discipline.** The cache is a pure memoization of the ONE `compute_setups` scan, not a second source of truth: the scan body is renamed `_run_full_panel_scan` with byte-identical logic (diff confirms only the return-tuple unpacking changed), and `compute_setups` stores and returns its output verbatim. All three consumers were traced and are strictly read-only over the shared object: `list_setups` builds NEW lists for every filter and never mutates event dicts (`routes.py:1882-1889`); `get_setup` enriches via copy-on-write (`enrich_with_tape_timeline` returns `{**event, ...}`, `setups.py:477-486`) and never mutates the cached event (`routes.py:1904-1909`); `edge_report._split_cells`/`_dataset_event` only iterate and read `events`, appending exclusively to local pools (`edge_report.py:298-305, 336-354`). The store signature (`_store_signature`, `:350-361`) keys on the per-series uuid `id` (`bars.py:244`) plus content `checksum`, so it busts on any real content change and — because the uuid is unique per `record()` — cannot collide across tests, which is why the spy-counter tests (`len(calls) == 1` / `== 2`) are robust rather than luck. Corrupt files are correctly excluded from both the signature and the scan, keeping them consistent. The dev's live cross-endpoint smoke (276.03s cold → 0.28-0.40s across all three endpoints, 13/801 real events flagged `reaction_boundary_truncated`) independently reproduces the exact iter-4 audit-B1 finding on the operator's real store.

**Frozen-foundation integrity.** `git diff --name-only -- apps/` touches only `setups.py` + `test_setups.py` + `test_setups_api.py`; every named frozen file (`levels.py`, `tradability.py`, `edge_report.py`, `backtests.py`, `bars.py`, `datasets.py`, `config.py`, `routes.py`, `engine/`, `adapters/`) is absent from the diff (verified directly). `config_fingerprint()` returns `4d665603569b9dbf` and the strategy registry is `('v1', 'structure_tape', 'structure_tape_map')` (both re-run independently). `test_setups_api.py`'s only change adds the two new field names to the exact-field-set assertion — confirming the route surfaces exactly the two additive fields and nothing else drifted.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT findings were identified. All findings are GAP/OBSERVATION-level (documented above); fixing them would be scope creep on a phase whose DoD is fully met. The full backend suite (1337 passed / 7 skipped / 0 failed) was independently re-confirmed by QA and the reviewer; this audit independently re-ran the change's blast radius (`test_setups.py`, `test_setups_api.py`, `test_edge_report.py`, `test_edge_report_api.py` — exit 0, clean) and the 7 named DoD tests (2 B1 boundary + extended pinned-AAPL + 4 B3 cache) — **7 passed**.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied — no CRITICAL/IMPORTANT issues found. |

---

## 5. Recommended Next Step

**Proceed to iter-6** — the pure-frontend J-05 `/structure` render on this now-recency-honest, now-bounded substrate. The two evaluator-named blockers are genuinely cleared: setups events additively disclose truncated horizons (13/801 real cases flagged), and the shared scan is served once from a byte-identical, store-checksum-keyed cache across all three endpoints, so a single J-05 page load stays within browser-QA timeouts. J-05 correctly remains `failing` this iteration; it must NOT be claimed until iter-6's real browser pass. Carry-forward for iter-6 (optional, non-blocking): if the frontend page-load fires the setups list and edge-report concurrently against a cold cache, consider the trivial atomic-rebind or lock from finding B1 to close the torn-read window — a one-line hardening, not a correctness prerequisite for a single operator.
