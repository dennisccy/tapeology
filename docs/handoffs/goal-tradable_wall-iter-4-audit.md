# goal-tradable_wall-iter-4 Audit Report

**Date:** 2026-07-14
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-04 — the honest 3-way edge report (`v1` vs frozen `structure_tape` vs the new registered
`structure_tape_map`) — is genuinely delivered: additive strategy registration with the config
fingerprint frozen, a band-armed backtest branch that leaves the frozen strategies byte-identical,
a canonical `GET /research/edge-report` + byte-identical read-only MCP proxy, and gate-integrity
guards (n≥5-or-`insufficient_sample`, never-pool-feeds, never-pool-train/hold-out, champion
untouched) that are enforced in code and covered by tight tests. I independently re-ran the full
suite (**1331 passed / 7 skipped / 0 failed / 0 errors**, exit 0), recomputed the fingerprint
(`4d665603569b9dbf`), and exercised the live endpoint (HTTP 200 honest-empty shape, POST → 405).
The disclosed judgment calls (feed as a 5th cell dimension; side-aware arming; a synthetic
companion for the populated-cell case) are all defensible, documented, and tested — none
compromise the phase goal. No critical or important gaps remain; no fixes were required.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): cell key is a 5-tuple (adds `feed`) beyond the DoD's literal 4-tuple**
`edge_report.py:_cell_key` / `_split_cells` key cells by `(strategy_id, band_class, band_side,
reaction, feed)`. The DoD names "strategy × class × side × reaction". The `feed` dimension is not
scope creep — it is the mechanism that satisfies the *critical* never-pool-across-feeds anti-goal:
a 4-tuple key would force two feeds' recordings into one cell (a rail violation) or require
rejecting mixed-feed registries (over-strict, unasked). Disclosed (dev handoff Known Issue #1),
flagged by the reviewer (NOTE), and proven by
`test_two_same_feed_datasets_pool_and_a_different_feed_never_pools` (`sim`/`iex` never merge). No
action.

**B2 — GAP (observation): the literal committed `datasets_j03/` fixture yields vacuously-empty cells; the populated cell structure is proven via a synthetic companion**
The committed fixture's symbol is `PG`, which is not in the config-owned 12-symbol panel, so it
resolves no owning `compute_setups` event → `train.cells == []`
(`test_keyless_committed_j03_fixture_with_the_real_panel_is_an_honest_empty_report`,
`edge_report.py:_dataset_event`). DoD item 1 ("integration test asserts the exact cell structure")
is met, but by `test_synthetic_scan_join_produces_real_cells_all_insufficient_sample` — which uses
`test_setups.py`'s synthetic scan under a test-local panel to produce three real cells (band_class
C, resistance, broke, feed sim; v1 n=1, tape/map n=0), each `insufficient_sample`. This is an
inherent property of the J-03-era fixture (recorded for the tape-join, not panel membership), is
honestly disclosed (Known Issues #2, #6), and the spec itself pre-declares an all-`insufficient_
sample` report a valid outcome. Both the vacuous-empty and the populated-insufficient cases are
covered. Acceptable known limitation, not a defect.

**B3 — GAP (observation): `GET /research/edge-report` can take minutes on a fully-populated real store**
`compute_setups` is *itself* the ~O(12 symbols × every stored session) full-panel scan the J-02 /
audit-B2 finding already named as ~4m43s. The literal hot-path guard the spec required IS
satisfied — `compute_setups` is called at most once per report and skipped entirely on an empty
registry (`run_strategy_comparison_report`; proven by
`test_compute_setups_runs_at_most_once_per_report_call`, 0 calls empty / 1 call non-empty). The
spec's NOTES only require keeping that scan off the per-request/per-dataset hot path, not making it
fast; caching is explicitly out of scope this iteration. Disclosed (Known Issue #5). Relevant to
J-05 (which renders this endpoint) and is a good caching candidate there — carried, not a J-04
defect.

**B4 — OBSERVATION (observation): `structure_tape_map` arming is side-aware; `structure_tape` is not**
`_structure_tape_map_side_for_reading` / `_structure_tape_map_arm` (`backtests.py`) only tests
bands on the semantically correct side (a rejection defends its side; a breakthrough moves through
the opposite). `structure_tape`'s zone-based arm has no side concept (a raw confluence zone carries
no side). This is a refinement, not a divergence from the archetype: a band *does* carry a side, so
testing it prevents a "breakthrough short" arming against a distant resistance band merely because
price sits below it. Additive to a brand-new strategy (structure_tape's branch is untouched and
byte-identical — verified B-tests below), disclosed (Known Issue #3), and proven both ways in
`test_structure_tape_map_side_aware_reading_never_arms_on_the_wrong_side_band` (with `structure_
tape`'s un-filtered arm as a positive control on the identical fixture). No action.

### Frontend Findings

N/A — backend-only iteration (`Frontend Present: no`). No UI surface changed; the `/structure` Edge
Report render is J-05. Browser checks correctly skipped.

### Test Findings

**T1 — OBSERVATION (observation): route→module byte-identity is proven only on an empty-cells payload**
`test_edge_report_api.py::test_edge_report_matches_the_module_function_byte_for_byte` records a real
PG dataset through `POST /research/datasets`, but PG yields `cells == []`, so the route-vs-module
byte-identity is exercised on an empty payload. The populated-cell *values* are proven at the module
level (`test_edge_report.py`) and the MCP byte-identity round-trip runs through a real subprocess
uvicorn backend. Serving-verbatim is a thin serialization concern that the empty payload exercises
adequately (all five top-level keys present). Adequate; could be marginally stronger with a
panel-symbol fixture. No action.

**T2 — OBSERVATION (observation): QA functional test-plan TC-12 mis-locates the 422 guard**
The QA test plan's TC-12 asserts `GET /research/edge-report?strategy_id=nonexistent` returns 422.
That route takes no `strategy_id` param, so FastAPI ignores the unknown query param and returns 200
— the plan's phrasing is wrong. The actual DoD requirement ("unknown strategy id refused 422") is
correctly met at `POST /research/backtests` and is covered by
`test_unregistered_strategy_id_is_still_422_never_coerced` (verified passing). QA marked TC-06-13
PASS "per dev handoff" rather than running the malformed curl, so no false green was produced
against the real endpoint. A QA-artifact imprecision, not an implementation defect. No product
action.

---

## 3. Domain Assessment

The core domain logic is correct and honest.

- **Arming (`backtests.py`).** `structure_tape_map` reads bands verbatim from the canonical
  `compute_tradability` owner as-of each event's own absolute timestamp (`epoch_anchor +
  point.timestamp`) — no lookahead, no second levels computation (statically guarded by
  `test_structure_tape_map_reads_tradability_never_recomputes_levels_or_zones`). Unclassified
  (`class: null`) bands never arm (no A/B/C to scale against) — proven with a classified-band
  positive control. The reused entry/exit/fee/slippage/size math is untouched; the inherited band
  class drives the class-scaled stops/rewards/size. Arming values are pinned by direct computation
  (exact `logical_ts`/price/class), not hand-derived.
- **Aggregation (`edge_report.py`).** Cells pool trades ordered by reconstructed real UTC entry
  time before the single reused `_aggregate` (so pooled `max_drawdown_r` is genuinely
  peak-to-trough in trade order). Train and hold-out are built from disjoint `_split_datasets`
  reads (structurally un-poolable); feeds are separated by the cell key. `n < pnl_min_sample_size`
  (5) → `insufficient_sample` — the gate is read from config, never lowered. The gate/ranking
  helpers (`_cell_beats_null`, `_cell_clears_gate`, `_surviving_train_cells`) are faithful twins of
  the era-3 `_beats_null`/`_is_positive_edge`/`_rank`, and `holdout_positive_edge` is honestly
  `False` on absent hold-out data (never a fabricated verdict).
- **Provenance/honesty.** The verbatim register string `simulated — assumed fees/slippage — not
  indicative of live results` is served (report-level, DRY — never restated); every cell carries
  both R and $ (a $ never exists without its R) plus its own null baseline; `feed` is stamped
  verbatim from the dataset. No profit/advice language. The report reads nothing that mutates state
  and never touches the champion pointer (verified).
- **Frozen foundations.** Independently verified: `config_fingerprint() == 4d665603569b9dbf`; no
  new `Config` field; `strategy_definition` returns the exact `structure_tape` grammar for the new
  id save the `strategy_id` value; `run_edge_report`/`main`/`_render_report` bodies untouched in the
  diff (only `_run_backtest` gained a backward-compatible `bar_store=None` kwarg); no `levels.py` /
  tape engine / `bars.py` / Alpaca-adapter file in the diff; zero credential literals in the diff.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issues were found. All findings are OBSERVATION- or GAP-level and are
documented above as known limitations/carries per the auditor scope rules.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

**Proceed to J-05.** The canonical `GET /research/edge-report` (+ MCP `edge_report`) read surface
exists, is byte-verified, and is ready to render. Two items should be carried into J-05 planning,
both already disclosed by the dev:

1. **Performance (B3):** rendering the Edge Report section on a populated store will hit the
   ~4m43s `compute_setups` scan. J-05 (or a dedicated iteration) should add a bounded
   cache/memoization for `compute_setups`, or scope the join to a snappier already-persisted scan,
   before the section reads live on every page load.
2. **Populated-cell demonstration (B2):** the only committed non-empty demonstration is synthetic
   (test-local panel). If a credentialed / panel-symbol recorded fixture becomes available (the
   J-03 operator-gated carry), re-verify the endpoint produces populated, correctly-labeled cells
   under the real panel.

Neither is a J-04 blocker. The response shape for J-05 is `{"register", "pnl_min_sample_size",
"train": {"cells": [...]}, "holdout": {"cells": [...]}, "surviving_train_cells": [...]}`; each cell
carries `strategy_id/band_class/band_side/reaction/feed/dataset_ids/measurement/null_baseline/
insufficient_sample`.
