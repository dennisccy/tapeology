# goal-fast_wall-iter-1 Audit Report

**Date:** 2026-07-17
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-01 ("stop the bleeding") is genuinely achieved: `GET /research/edge-report` is now rewired
through `peek_strategy_comparison_report`, which on a cold cache with a non-empty registry returns
an honest `status: "not_computed"` payload and provably NEVER enters the sweep — I independently
confirmed the compute-spy records **zero** calls to `_compute_strategy_comparison_report`, the
`/structure` panel renders correctly in live browser DOM (I viewed the screenshots myself), and
the frozen foundation is intact (fingerprint `4d665603569b9dbf`, `get_or_compute` + its 16 tests
byte-unchanged, tier-1 no-execution-path guard green). The gaps are minor, disclosed, and
non-blocking: one MCP byte-identity test (TC-6) was made order-coupled this iteration (fails in
isolation but passes loudly-or-green in the canonical run), and the not-computed payload's
`dataset_count` is fetched but not rendered (the binding DoD only requires `detail`). No CRITICAL
or IMPORTANT issue was found; no fix was warranted.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION: the no-compute-on-GET guarantee is correct and well-guarded.**
Traced `peek_strategy_comparison_report` (`apps/backend/app/research/edge_report.py:487-526`) end
to end. Only ONE branch calls `_compute_strategy_comparison_report`: the empty-registry case
(line 515), which is genuinely O(1) — `_compute_strategy_comparison_report` skips `compute_setups`
and every backtest when both splits are empty (`edge_report.py:548-550`, `if train_datasets or
holdout_datasets:`). The non-empty cold path returns a dict literal via the read-only
`cache.lookup` (`edge_report_cache.py:301-322`), which has no `compute_fn` parameter and is
mechanically incapable of starting the sweep. `register` is read from `backtests.REGISTER`
(`edge_report.py:523`), never a restated literal. This is exactly the interlude's headline
anti-goal, correctly enforced. No action.

### Frontend Findings

**F1 — GAP (disclosed): `dataset_count` is fetched and typed but never rendered.**
The not-computed payload carries `dataset_count` (`lib/types.ts:1371`), and the phase spec's "New
information displayed" prose (spec line 71) states both `detail` AND `dataset_count` "become newly
visible." `NotComputedPanel` (`apps/frontend/app/structure/page.tsx:287-297`) renders only the
headline + `detail`. This does NOT violate any binding acceptance criterion: the DoD's TC-11, the
Frontend IN SCOPE bullet (spec line 62), and the browser test all require only the headline +
verbatim `detail`, which are met (verified in UT-02, byte-identical to the backend JSON). The
omission is disclosed identically in the dev handoff, frontend handoff, and ux-regression report.
Not fixed — rendering `dataset_count` was not required by any DoD item and has no existing UI slot;
adding it would be an unrequested UI change (scope creep). Carry to a future iteration if desired.

**F2 — OBSERVATION: not-computed and unavailable panels are visually indistinguishable.**
`NotComputedPanel` reuses `UnavailablePanel`'s exact amber Tailwind classes verbatim
(`page.tsx:287-297` vs `254-266`), so a benign "not computed yet" state and a genuine backend
failure differ only by text. This is a deliberate, reasoned "no new visual language" tradeoff
mandated by the spec's Design Direction (spec line 62 / plan Visual Requirements) and disclosed in
the frontend handoff — introducing a third color treatment would itself be a design-system
deviation. Advisory only for J-04 when a compute trigger lands in this panel. No action.

### Test Findings

**T1 — GAP: the TC-6 MCP byte-identity test was made order-coupled this iteration.**
`test_edge_report_tool_byte_identical_to_rest` (`apps/backend/tests/test_mcp_server.py:539-562`)
now opens with `assert len(datasets) >= 1, "an earlier test in this module must have already
registered one"` and asserts the `not_computed` shape. This depends on an unrelated earlier test
(`test_datasets_tool_byte_identical_on_a_non_empty_live_list`, line 251) having registered a
dataset into the **module-scoped** shared backend (`watched_backend`, `scope="module"`, line 148).
Before this iteration the test was order-INDEPENDENT (it asserted the full-report shape, present
whether or not datasets existed). I reproduced the failure: run in isolation it fails
`assert 0 >= 1`. **However** — (a) the canonical `pytest tests/test_mcp_server.py` run passes
(I verified: 28 passed), (b) the actual product byte-identity assertion
(`result.content[0].text.encode("utf-8") == rest.content`) is intact and genuinely correct, so
TC-6 IS proven in the pipeline's real invocation, (c) it fails LOUDLY via an explicit precondition
assert, never a silent false-green, and (d) file-order state accumulation is a pre-existing,
pervasive design of this module (the very next test, line 583, tolerates `409 = already recorded by
an earlier test`). Not fixed: de-coupling one test inside a module that is architecturally built on
ordered shared-backend state would be inconsistent scope creep and risks perturbing downstream
count assumptions. Recommend a future cleanup to self-seed this test's own dataset. Weighed
IMPORTANT vs GAP; chose GAP because the product is correct, the canonical gate passes, and the
failure mode is loud, not a false-green.

**T2 — OBSERVATION: the QA report under-reports the browser evidence that actually exists.**
The QA report (`reports/qa/goal-fast_wall-iter-1-qa.md:93-98`) marks TC-11/TC-12 as **SKIP**
("browser session timed out"), and `status.json` says `browser_checks_run: false`. But the
browser-qa-agent's own `reports/phase-goal-fast_wall-iter-1-ui-test-results.md` records **7/7
PASS** with live DOM captures for exactly these states (UT-02 = TC-11 cold not-computed panel;
UT-03 = TC-12 warm frozen empty state on a scoped pre-warmed fixture), and the evidence PNGs are
real (I opened UT-02 and UT-03 and confirmed the correct amber "Edge report not computed yet."
panel and the slate "No edge-report cells yet." + register banner respectively). So the DoD's
browser requirement is genuinely met; the QA "SKIP" reflects only that agent's separate,
superseded attempt. A reporting inconsistency, not a product defect. No action.

### Positive verifications (independently reproduced this audit)

- **Compute-spy / TC-2**: `test_edge_report_cold_cache_returns_the_not_computed_payload_and_never_computes`
  asserts `calls == []` — ran and passed. The mechanical heart of J-01 holds.
- **Warm byte-identity / TC-4**: `test_edge_report_matches_the_module_function_byte_for_byte`
  (pre-warms via `compute_and_publish`, then `json.dumps(..., sort_keys=True)` equality) — passed.
- **peek branches / integrity bypass**: 5 peek tests passed, including one that tampers a checksum
  AND monkeypatches `cache.lookup` to raise if touched (proving the integrity path bypasses the
  cache entirely, spec TESTING error-case).
- **Cache layer / TC-8–TC-10**: full `test_edge_report_cache.py` — 25 passed (16 untouched + 9 new).
- **MCP module / TC-6, TC-14**: full `test_mcp_server.py` in canonical order — 28 passed.
- **Fingerprint / TC-15**: `config_fingerprint()` == `4d665603569b9dbf` — reproduced.
- **J-07 sentinel**: engine/profile equivalence (22 passed per QA) + deterministic replay UT-J-07
  PASS; the old always-compute hazard code path no longer exists (compute-spy is the proof).
- **Tier-1 anti-goal**: `test_no_execution_path.py` — 6 passed.
- **routes.py hygiene**: no live reference to the removed `run_strategy_comparison_report` (only a
  comment survives); `os` import still used elsewhere (not dead); all four pinned
  `Depends(...)` + `cache=cache` present in `get_edge_report`.

---

## 3. Domain Assessment

The core domain logic is correct and honest. The design splits `get_or_compute`'s "check-then-
compute" into two named halves — a read-only `lookup` (the GET path's sole method) and a
write-only `compute_and_publish` (J-04's future force path) — sharing the identical `_cache_key`
derivation and store-integrity-bypass discipline as the untouched `get_or_compute`. This makes the
"no compute on a GET" guarantee a structural property (the route can reach no method that computes),
not merely a runtime check, and it is pinned by a source-introspection guard
(`test_peek_source_never_calls_a_compute_triggering_cache_method`). The accelerator anti-goals hold:
the warm path serves `_compute_strategy_comparison_report`'s output verbatim (TC-4 byte-identity),
`_insert` deliberately avoids `sort_keys` so a SQLite-served warm response is byte-identical to a
fresh uncached one (preventing divergent accelerator output), and the not-computed payload reads
`register` from the canonical constant. The empty-registry branch correctly preserves the exact
pre-J-01 O(1) shape with no `status` key. The honest interim limitation — a real-corpus cold GET
still costs ~29s for the unaccelerated `dataset_store.list()` (J-02's future scope) — is exactly
what the spec anticipated and is bounded by `list()`, never by the sweep; the dev's live check
measured 28.9s with backend CPU dropping to 0.5% immediately after (no lingering sweep) and no
cache DB created. The frontend discriminated union (`EdgeReportPayload`) and the render branch
ordering (not_computed checked strictly before `EdgeReportBody`) are sound.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found. All findings are GAP- or OBSERVATION-level, which
per the auditor protocol are documented (above) rather than fixed — fixing them would be scope
creep on a phase whose binding DEFINITION OF DONE is fully met.

---

## 5. Recommended Next Step

**Proceed to the next iteration (J-02).** The phase goal is fully achieved and the frozen
foundation is verifiably intact. Carry these non-blocking notes forward:

1. **(T1, future cleanup)** When J-02+ next touches `test_mcp_server.py`, self-seed
   `test_edge_report_tool_byte_identical_to_rest`'s own dataset so TC-6 no longer depends on an
   earlier test's side effect (the downstream test at line 583 already tolerates a `409`, so this
   is safe).
2. **(F1, optional UI)** If `dataset_count` visibility is genuinely wanted per the spec's "New
   information displayed" prose, add it explicitly in a later iteration — it was correctly left out
   here as no binding criterion required it.
3. **(F2, J-04 design)** When J-04 adds the "Compute edge report" trigger into this exact panel,
   revisit whether the not-computed vs unavailable amber states need a copy/affordance
   differentiator now that an operator action resolves one but not the other.
