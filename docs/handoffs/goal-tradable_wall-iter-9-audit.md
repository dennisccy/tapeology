# goal-tradable_wall-iter-9 Audit Report

**Date:** 2026-07-15
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal — wrapping `run_strategy_comparison_report`'s ~10+h sweep in a rebuildable,
checksum-keyed, restart-durable result cache that serves `GET /research/edge-report` byte-identically
to a fresh compute, never as a second source of truth, champion untouched — is **achieved and verified
first-hand at the machinery level**. The cache's hard parts (torn-read safety, restart durability,
byte-identity on a non-degenerate shape, six-way key-busting, single-computation-path coherence,
frozen-foundation invariance) are all real, correctly implemented, and covered by tight tests I ran
myself. The **one gap** is that the headline user payoff — watching a warm Edge Report *resolve* fast
in a browser — was again not observed (only the loading state), because the QA backend ran against the
real corpus with a cold ~10h compute in flight. That gap is deliberately operator-gated by the spec's
own Interpretation call, is proven at the route/HTTP level instead, and is disclosed honestly in every
artifact — so it does not compromise the goal, but it is a real, third-consecutive-iteration limitation
worth recording.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): the in-process fast path never persists across requests in production**
`routes.py:1564` `get_edge_report_cache()` constructs a fresh `EdgeReportCache` per request (no
`lru_cache`/singleton), so the instance-scoped `_hot` tuple (`edge_report_cache.py:173`, `254-265`) is
always `None` at the start of each request and is discarded after it. In production the warm-serve and
torn-read guarantees therefore rest **entirely on the durable SQLite layer** (`_select`, `edge_report_cache.py:191`),
which is correct: a warm request is one point-query on a primary key (sub-millisecond), and the atomic
`INSERT OR REPLACE` inside `with conn:` (`edge_report_cache.py:217-226`) is the torn-read guard that
actually fires cross-request. The in-process tuple is only exercised within a single `get_or_compute`
call and by the 16-thread concurrency test (which shares one instance). This is the reviewer's NOTE;
it is a harmless redundancy, not a correctness issue, and fixing it (memoizing the dependency) is an
optional future optimization, not this iteration's concern. No fix applied.

**B2 — OBSERVATION (observation): the cache key is four parts, not the three the plan named — and this is the correct call**
`edge_report_cache.py:141-154` folds a fourth component — a hash over the *entire* `Config` field
content (`_config_content_hash`, no exclusion set) — beside the plan's three (dataset checksums,
`strategy_registry()`, `config_fingerprint()`). I traced the dev's stated staleness bug and confirm it
is real: `config_fingerprint()` deliberately excludes `pnl_min_sample_size` and the
`sr_*`/`tradability_*`/`setups_*` families (verified in `config.py`), yet `_split_cells`
(`edge_report.py:371`) bakes `pnl_min_sample_size` into every cell's `insufficient_sample` and
`compute_setups` reads the tradability/level parameters. Without the 4th component, changing
`pnl_min_sample_size` would silently serve a stale report. The 4th component only ever makes the cache
*more* conservative (it can never cause a stale serve), and I confirmed it is **stable across a real
restart**: every `Config` path field (`dataset_dir`, `bar_dir`, `pnl_history_md_path`) is a static
`Path(__file__).resolve()` default baked at import — never an env-resolved value (the env overrides live
in `*_resolved()` methods, not the fields) — so `dataclasses.asdict(CONFIG)` is byte-stable across
restarts on the same install, and durability holds. This is a justified correctness improvement, flagged
honestly as a deviation, with two dedicated proving tests (`test_pnl_min_sample_size_change_busts...`,
`test_tradability_field_change_busts...`, both verified passing). No fix warranted.

### Frontend Findings

**F1 — GAP (gap): the warm-cache Edge Report render was not observed end-to-end in a browser**
The J-08 headline experience — the Edge Report section *resolving* to the 3-way register (or the honest
all-`insufficient_sample`/empty state) within an interactive budget — was **not** browser-observed this
session. `reports/phase-goal-tradable_wall-iter-9-ui-test-results.md` records UT-01 PASS (loading state
only: `data-testid="edge-report-loading"`, exact caption text) and UT-02/UT-03/UT-06 **SKIP** under the
pre-authorized cold-cache carve-out, because the browser-QA agent directly confirmed the cache was
genuinely cold the entire session (0 rows in `edge_report_cache.db` at start and ~1h later; backend
pinned 90–100% CPU with ~59 min accumulated compute; `curl` no-response within 45s). This is the third
consecutive iteration (iter-6/iter-8/iter-9) where no one has watched a populated Edge Report finish
rendering.

I weighed this as **IMPORTANT** — the spec's own NOTES section says "the warm-cache render must be
observed in a real browser… not left to a loading carve-out," and it *was* left to a loading carve-out —
but land on **GAP**, for three evidence-based reasons: (1) the spec's explicit *Interpretation call*
("J-08's passing bar is its keyless core… with the first real ~10+h compute treated as the operator-gated
carry… A human who requires the real compute… could reverse this to `partial`") pre-authorizes exactly
this reading, mirroring the accepted J-03/J-04 credentialed carries; (2) the warm-serve guarantee is
independently proven at the HTTP-route level — I ran
`test_edge_report_route_serves_a_warm_result_on_the_second_call_without_recomputing` and
`test_edge_report_route_response_is_byte_identical_whether_cache_is_cold_or_warm`, both pass, and the
frontend handoff + UT-01 confirm the section reads every field verbatim off the response with no client
timeout; (3) it is disclosed prominently and consistently across `ui-test-results.md`, the ux-regression
report, `user-visible-changes.md`, and the dev handoff — never over-claimed as done. It is a real
operator-gated limitation, not a defect. I did not close it by spinning up a keyless scoped browser
stack: the machinery is already route-proven, the render path is unchanged J-05 code, and my dispatch
scope directs assessment from code + tests rather than heavy long-running verification (the pipeline
backend is at 100% CPU on the real compute). No fix applied.

### Test Findings

**T1 — OBSERVATION (observation): the QA report's TC-01 row reads slightly more favorably than the browser evidence**
`reports/qa/goal-tradable_wall-iter-9-qa.md` TC-01 records "Page loads, Edge Report section present and
renderable … PASS" against an expected "Response within ≤5s, fully rendered cells or honest empty state."
The browser reality (per the browser-QA agent's own UT-01/UT-02) is that only the *loading* state was
seen; the resolved render was a documented SKIP. The QA report does disclose the truth elsewhere (TC-02
"times out due to ~10+h compute," Known Limitations #1), so this is a phrasing generosity in one summary
row, not a fabricated pass. No product impact; noted for honesty only.

---

## 3. Domain Assessment

The core engineering is strong and, unusually for a "just add a cache" iteration, gets the subtle parts
right:

- **Torn-read safety is genuinely mirrored, not cargo-culted.** `get_or_compute` (`edge_report_cache.py:254-265`)
  uses the exact `setups.py` `_SCAN_CACHE` iter-6 pattern — read `self._hot` into one local before
  inspecting, publish a complete `(key, result)` tuple in a single rebind — layered over an atomic
  `INSERT OR REPLACE` transaction. The 16-thread barrier-synchronized cold-cache test with an injected
  publish-window sleep genuinely bites and asserts byte-identical results across all threads (verified
  passing).
- **Byte-identity is preserved at the one place it matters.** The stored blob is serialized *without*
  `sort_keys` (`_insert`, `edge_report_cache.py:201-224`), while `_canonical` (sorted) is used for
  hashing only — the dev's caught-and-fixed real bug. The dedicated regression test
  (`test_result_key_order_is_preserved_through_the_durable_round_trip_not_merely_content_equal`) picks a
  key that would sort out of position, and the `test_mcp_server.py` raw-wire-byte tests pass — so REST,
  MCP, and durable-cache-hit responses are provably identical bytes.
- **The cache owns nothing.** The public `run_strategy_comparison_report` is a thin dispatcher over
  `_compute_strategy_comparison_report` (`edge_report.py:427-457`); `cache=None` is byte-identical to the
  pre-J-08 path; a miss recomputes through the caller's own `compute_fn`. Coherence guards
  (`test_cache_source_never_computes_a_research_value_itself`,
  `test_cache_wiring_source_never_duplicates_the_computation`) enforce this structurally and pass. A
  store-integrity failure bypasses the cache entirely and caches nothing (`get_or_compute` line 249-251;
  `test_store_integrity_error_bypasses_the_cache_and_persists_nothing`), so a corrupt dataset can never
  poison or be served from the cache.
- **PnL-history append is a faithful verbatim-copy writer.** `append_strategy_comparison_row`
  (`pnl_ledger.py:218-297`) deep-copies each cell, adds only `basis`, never sums/averages/merges, keeps
  train/holdout and feeds separate, carries the `REGISTER` ("simulated — assumed fees/slippage — not
  indicative of live results", `backtests.py:144`) and the row-level assumptions, and refuses malformed
  reports with `LedgerCompositionError`. The existing two-way row branch is untouched and its rendered
  output is proven byte-identical whether or not a new 3-way row follows it.
- **Frozen foundations are intact.** `git diff HEAD` is empty for `levels.py`, `setups.py`,
  `tradability.py`, `backtests.py`, `config.py`, all of `apps/frontend/`, and the committed
  `reports/pnl/pnl-history.md`; I independently recomputed `config_fingerprint() == 4d665603569b9dbf`;
  the champion-pointer-untouched invariant is tested through the cached path. Anti-goals hold
  (no-credential test green; descriptive register present; additive-only, no frozen mutation).

**First-hand test evidence I gathered (not relied on from the handoff):**
- Full backend suite: **1399 tests, exit 0** (1392 passed / 7 skipped / 0 failed) — the 7 skips are the
  pre-existing `integration`-marked live tests; iter-8 baseline was 1348 passed / 7 skipped, so +44
  passing, 0 new skips, 0 regressions. No `@pytest.mark.skip`/`pytest.skip` added in any new/changed test
  file.
- Cache + edge-report + api + pnl subset: **98 passed**; equivalence + no-credential + observer + MCP:
  **54 passed**; the determinism, concurrency, durability, and warm-route tests each pass when run
  explicitly.

J-05 (Tradable Map: pinned AAPL 2026-06-22 band `300.17–302.27` Class A score 153, 10 rows, raw-toggle
off by default) and J-06 (cockpit SIM/Live/Historical across 4 real SIP windows) were positively
re-verified by browser-QA with DOM/screenshot evidence — closing the J-05 verification gap iter-8's UX
review had flagged.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT defect was found; the implementation is surgical, additive, correct, and
honestly documented. Applying changes for the OBSERVATION/GAP items would be scope creep.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

**Proceed.** The cache machinery — the actual deliverable of this iteration — is complete, correct, and
first-hand verified; the enhancement-loop journey J-08 is met at the keyless-core bar the spec defined.

Carry one documented, operator-gated item forward (already recommended verbatim by the ux-regression
review, not a new blocker): **the operator should warm `GET /research/edge-report` once for real over the
11 credentialed `sip` datasets, then re-run the browser check** to (a) confirm `/structure`'s Edge Report
panel resolves within seconds (closing UT-02/UT-03/UT-06), (b) refresh to confirm it stays fast across a
restart, and (c) re-check UT-11's open band-overlay/confluence-chip observation now that the edge-report
dependency it plausibly gates on would be populated. If and when that real compute completes, the same
operator step can append its register to `reports/pnl/pnl-history.md` via
`python -m app.research.pnl_history --append-report <json> --enhancement-id <id> --title <title>` (the
tested, keyless-built machinery is ready). A future iteration that performs that real append should also
add a `/structure` render path for the new `kind: "strategy_comparison"` ledger row, which currently has
no UI home.
