# goal-fast_wall-iter-5 Execution Plan

Session `fast_wall`, iteration 5, depth **full**. Target journeys **J-04** (browser re-verification
only, zero new code) and **J-05** ("the sweep becomes resumable and parallel"). Required-still-passing:
J-01, J-02, J-03, J-07. Full detail, acceptance criteria, and the TC-1..TC-14 test-first contract live in
`docs/phases/goal-fast_wall-iter-5.md` — the developer must read that file in full; this plan is a guide,
not a restatement.

**Alignment check:** J-04 and J-05 are both named verbatim in `docs/goal.md`'s Must-have user journeys
(same IDs, same descriptions, same dependency order J-01→J-02→J-03→J-04→J-05). J-05 directly serves
Success Criteria #4 ("the first full real edge report completes... resumable... and parallel"). No drift
from the project goal; no scope creep — the phase spec's own OUT OF SCOPE section is unusually explicit
and this plan carries it forward unchanged.

## What to Build

**1. Verification only (zero product code change) — closes J-04's last gap:**
Re-run browser-qa against a FRESH scoped backend/frontend pair (the established ports 8391/3391 recipe:
fresh temp journal/dataset/bar dirs, `TAPEOLOGY_DATASET_DIR` pointed at the committed
`apps/backend/tests/fixtures/datasets_j03` fixture, cold edge-report cache — NEVER the default
`.data/datasets` 882MB corpus). This iteration's scoped env must ALSO set
`TAPEOLOGY_EDGE_SWEEP_CACHE_DB` alongside the existing `TAPEOLOGY_EDGE_REPORT_CACHE_DB`, so J-05's new
durable cache never touches `.data/` either.
- TC-1: click "Compute edge report" → screenshot mid-run (progress counts visible while
  `state === "running"`) → screenshot of the terminal render, within 90s, zero full-page reload.
- TC-2 (same session): J-01's not-computed panel render (before the click) + J-07's broader
  `/structure` sections (Tradable Map, Case Studies, Registry, Comparison) rendering exactly as shipped.
- TC-3: a `state: "failed"` snapshot (arranged via a direct backend call before navigation) renders its
  exact `error` string verbatim.

A single passing screenshot set flips J-04 `partial → passing` with **no new product code** — iter-4
already built and audited the button/poll/panel logic end-to-end (121 targeted tests, curl lifecycle);
this is a re-verification pass only, blocked twice before by an environmental Chrome MCP failure
reproduced independently by 4 agents in iter-4.

**2. Backend — J-05 "resumable + parallel sweep":**
- New `EdgeReportBacktestCache` (new module — e.g. `edge_report_backtest_cache.py` — or co-located in
  `edge_report_cache.py`, developer's choice): one durable SQLite row per (dataset × strategy) pair. Key
  = sha256 of canonical JSON of `{dataset_id, dataset_checksum, strategy_id, profile, config_fingerprint,
  config_content_hash, strategy_registry, bar_store_signature}`. Reuse `_canonical`/`_config_content_hash`
  from `edge_report_cache.py` verbatim — never re-derive. `bar_store_signature` reuses
  `setups._store_signature(bar_store)` verbatim (currently private; export/alias if needed), computed
  ONCE per sweep, never once per pair. Values = the runner's own per-pair `result` block, stored WITHOUT
  `sort_keys` (mirrors `EdgeReportCache._insert`'s byte-identity discipline). Path: env
  `TAPEOLOGY_EDGE_SWEEP_CACHE_DB` else `.data/edge_report_backtests.db` sibling of the dataset dir
  (mirrors `resolve_cache_db_path`). `lookup(key)`/`publish(key, result)`, WAL + busy_timeout.
- `edge_report.py`: `_split_cells` gains a `run_pair(dataset_meta, strategy_id)` provider seam, default
  `None` → byte-identical to today's inline `_run_backtest` call; pooling/ordering/aggregation code stays
  untouched. `_ProgressReporter` distinguishes a sub-cache hit from a fresh compute so
  `backtests_from_cache` (emitted since J-04, currently always 0 — dead) genuinely increments.
  `run_strategy_comparison_report`/`_compute_strategy_comparison_report` build the caching `run_pair`
  provider whenever `sub_cache` is supplied — the SAME provider/cache instance serves BOTH the train and
  hold-out `_split_cells` calls (implementation hint in the spec's NOTES: build it as a closure over the
  reporter/cache already in scope; compute `bar_store_signature` once outside the pair loop).
- Parallel provider (**CLI-only this iteration** — see Scope Decision below): `ProcessPoolExecutor` with
  the `spawn` context; task = one dataset (all three strategies); largest-first (LPT) scheduling by event
  count; `workers` from `--workers N` (default env `TAPEOLOGY_EDGE_SWEEP_WORKERS` else the existing
  `_DEFAULT_WORKERS = 4`, documented ceiling ~6). Each worker builds its own stores from explicit paths,
  uses a throwaway temp journal DB for job bookkeeping, publishes each completed pair to the durable
  sub-cache the instant it finishes. The orchestrating process reassembles via the SAME untouched
  `_split_cells`/`run_pair` sub-cache-hit path — byte-identical by construction. Cancellation stops
  submitting new tasks and lets in-flight tasks persist their pairs.
- `edge_report_compute.py`: CLI `main()` constructs a real `EdgeReportBacktestCache` and passes
  `sub_cache=<cache>` alongside the already-passed `workers=args.workers`.
  `EdgeReportComputeManager.trigger()` gains a new keyword-only `sub_cache: EdgeReportBacktestCache | None
  = None` (default preserves every existing caller/test byte-for-byte), threaded into its own
  `run_strategy_comparison_report` call inside `_work()` — a browser-triggered compute becomes resumable
  too. `trigger()` must NEVER pass `workers` above `1`/`None`.
- `routes.py`: new `get_edge_report_backtest_cache()` dependency resolver (the `get_edge_report_cache`
  precedent), threaded into `trigger_edge_report_compute` so the manager's `trigger()` call receives a
  real `sub_cache` — no second store/cache construction path.
- Tests: new module for `EdgeReportBacktestCache` (key-busting matrix over all 8 components, WAL
  durability, cache-loss recompute); `test_edge_report.py` additions (`run_pair` default-equivalence,
  kill-and-resume spy, new-dataset-costs-exactly-three); `test_edge_report_compute.py` additions (CLI
  `--workers 2` byte-identity + multi-process spy, manager `sub_cache` wiring/resumability, the
  "manager never passes `workers>1`" guard). Re-run byte-unmodified: the existing source-introspection
  guards (`test_backtests.py:1500-1508`/`:932-943`, `test_setups.py:995-1017`/`:758-771`) and
  `test_advertised_tool_set_is_exactly_capability_6` (`test_mcp_server.py`).

**3. Frontend: none planned.** `Frontend Present: yes` is set solely to force the UI Impact / UI Test
Design / Browser QA / UX Regression lanes to run this iteration against the EXISTING, already-shipped
`/structure` button/panel (`structure/page.tsx`, byte-unchanged since iter-4) — the goal is capturing
J-04's still-missing screenshot, not shipping new frontend code. A cold click's visible behavior is
unaffected by J-05's sub-cache wiring (a cold sub-cache looks identical to no sub-cache on a fresh
session's first run).

## Out of Scope (verbatim from phase spec — do not relitigate)

- J-06 (`setups_scan_cache.py`) — independent of J-05, a separate future iteration.
- Wiring `workers > 1` into `EdgeReportComputeManager.trigger()`/the button path — see Scope Decision
  below; CLI-only this iteration, reversible later with no signature-breaking change.
- Running the CLI warmer to completion against the FULL real corpus + appending to
  `reports/pnl/pnl-history.md` — *(operator-verified on the real corpus)* only, bonus non-blocking
  evidence if time/CPU allows, never required for this iteration's Definition of Done.
- Any change to `levels.py`/`tradability.py` (J-03's files), `bars.py`/`datasets.py`/`dataset_index.py`
  (J-02's files), `app/mcp/__init__.py` (no new MCP tool — REST + CLI only), or `EdgeReportCache`'s
  existing `get_or_compute`/`lookup`/`compute_and_publish` method **bodies**.
- Any new `/structure` UI element, any new `Config` field, any new runtime dependency beyond stdlib
  `sqlite3`/`concurrent.futures`/`multiprocessing`.
- Deleting or weakening any existing test.

## Scope Decision Already Logged (do not re-derive)

`runs/goal-session-fast_wall/state/assumptions.md`'s iter-5 entry already resolved the one real
ambiguity in this iteration's scope: `sub_cache=` (resumability, pure SQLite, no new concurrency
primitive) is wired into BOTH the CLI warmer and `EdgeReportComputeManager.trigger()`. Genuine
`workers > 1` process-pool parallelism is wired into the **CLI warmer only** —
`ProcessPoolExecutor`/multiprocessing must never enter the always-on FastAPI/uvicorn backend process.
This is deliberate, reversible, and already accepted — do not reopen it during implementation or review.

## Agents Required

- developer: yes — implements J-05's backend (new `EdgeReportBacktestCache` module + tests, the
  `run_pair` seam in `edge_report.py`, the CLI-only `ProcessPoolExecutor` parallel provider in
  `edge_report_compute.py`, `sub_cache` wiring into both `trigger()` and CLI `main()`, the new
  `routes.py` dependency resolver), AND performs the zero-code J-04/J-01/J-07 browser re-verification
  pass (TC-1/TC-2/TC-3) against the scoped fixture backend/frontend pair. This project's agent roster
  has one implementation agent (`developer`) covering both backend and frontend/browser-verification
  work — no separate backend/frontend agents exist here. No frontend product-code changes are expected;
  `structure/page.tsx` should stay byte-unchanged (`git diff` on `apps/frontend/**` should be empty).

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/research/edge_report_backtest_cache.py` (NEW, or co-located inside
  `edge_report_cache.py`) — `EdgeReportBacktestCache` class.
- `apps/backend/app/research/edge_report.py` — `_split_cells`'s `run_pair` seam (currently
  `edge_report.py:405-481`); `_ProgressReporter`/`pair_done()` cache-hit distinction (currently
  `edge_report.py:371-402`); `run_strategy_comparison_report`/`_compute_strategy_comparison_report`
  build the caching provider when `sub_cache` is supplied (currently `edge_report.py:534-707`); the
  parallel provider (or a helper it calls from `edge_report_compute.py`).
- `apps/backend/app/research/edge_report_compute.py` — CLI `main()` (currently lines 244-299) wires
  `sub_cache=`; `EdgeReportComputeManager.trigger()` (currently lines 116-181) gains the `sub_cache`
  kwarg, never passes `workers>1`.
- `apps/backend/app/research/routes.py` — new `get_edge_report_backtest_cache()` dependency (the
  `get_edge_report_cache` precedent at routes.py:1598-1612); `trigger_edge_report_compute` (routes.py
  ~2176-2192) wiring.
- `apps/backend/app/research/setups.py` — export/alias `_store_signature` only if the developer judges
  it necessary (Python does not enforce the leading-underscore convention at import time; a straight
  `from .setups import _store_signature` works today — prefer that over duplicating the tuple shape).
- `apps/backend/tests/test_edge_report_backtest_cache.py` (NEW) — key-busting matrix (8 components),
  WAL durability, cache-loss recompute.
- `apps/backend/tests/test_edge_report.py` — `run_pair` default-equivalence, kill-and-resume spy,
  new-dataset-costs-exactly-three.
- `apps/backend/tests/test_edge_report_compute.py` — CLI `--workers 2` byte-identity + multi-process
  spy, manager `sub_cache` wiring/resumability, the never-`workers>1` guard.
- `docs/handoffs/goal-fast_wall-iter-5-dev.md` — dev handoff (required).
- **Zero diff expected:** `levels.py`, `tradability.py`, `backtests.py`, `bars.py`, `datasets.py`,
  `dataset_index.py`, `edge_report_cache.py` (method bodies — imports of `_canonical`/
  `_config_content_hash` are fine), `app/mcp/__init__.py`, `config.py`, and every file under
  `apps/frontend/`.

## UI Evolution (Frontend Present: yes)

- New user-facing capability: none new. J-05 accelerates the EXISTING "Compute edge report" button
  invisibly — a re-triggered compute now survives a kill without redoing finished pairs, and the CLI
  warmer's `--workers N` genuinely parallelizes instead of silently accepting-and-ignoring the flag.
  J-04's already-shipped capability becomes fully **verified** (browser screenshot) rather than
  partially verified.
- New information displayed: none new. The compute snapshot's `progress.backtests_from_cache` field
  (already rendered since iter-4) starts reporting genuine nonzero counts on a resumed run instead of
  always reading 0.
- New user actions: none — the existing "Compute edge report" button is byte-unchanged.
- UI surface changes: none — `/structure`'s Edge Report section is byte-unchanged this iteration.
- Navigation changes: none.

## Visual Requirements (Frontend Present: yes)

- Component patterns: reuse `NotComputedPanel` / `EdgeReportBody` / `UnavailablePanel`'s amber
  degraded-state container exactly as shipped in iter-4 — no new components, no new Tailwind classes.
- Layout: unchanged — `/structure`'s existing Tradable Map / Case Studies / Edge Report section order.
- Key visual effects: none new — dark-only, dense, terminal-grade (Design Direction unchanged); no new
  visual language, per the phase spec.
- States to handle (already implemented, this iteration only needs screenshots): idle → running
  (progress line `backtests_done / backtests_total` + from-cache annotation) → failed (verbatim error,
  "Retry compute") → done (falls through to the pre-existing `EdgeReportBody`). Also capture: J-01's
  not-computed panel pre-click, and J-07's Tradable Map / Case Studies / Registry / Comparison sections.

## Key Test Scenarios

(Condensed — full acceptance detail and exact TC numbering in `docs/phases/goal-fast_wall-iter-5.md`.)

- TC-1/2/3 (browser, scoped 8391/3391 fixture backend, cold cache): compute click → progress mid-run →
  terminal render within 90s with zero full-page reload; J-01 not-computed panel + J-07's broader
  `/structure` sections render exactly as before; a `state: "failed"` snapshot renders its exact error
  string verbatim.
- TC-4: a fresh empty `EdgeReportBacktestCache` + a full sweep run publishes every eligible pair
  durably, and the returned report is byte-identical (`sort_keys=True`) to the same inputs run with
  `sub_cache=None`.
- TC-5 (non-vacuous key-busting matrix): each of the 8 key components, mutated independently, busts a
  cached pair — a call-counting spy on `_run_backtest` records a NEW call for every one of the 8.
- TC-6 (kill-and-resume): a sweep aborted mid-run after publishing N pairs, re-triggered with the SAME
  `sub_cache`, makes fresh calls ONLY for the remaining pairs; `backtests_from_cache == N`.
- TC-7 (new dataset costs three): a warm sub-cache + one newly registered dataset costs exactly 3 new
  `_run_backtest` calls, zero for every pre-existing dataset.
- TC-8 (parallel equivalence, non-vacuous): sequential (`workers=None`) vs CLI `--workers 2` over ≥2
  datasets, each against a fresh empty sub-cache — byte-identical reports AND a spy proving ≥2 distinct
  worker process ids were actually used (never a silent sequential fallback).
- TC-9 (cache loss is harmless): deleting the sub-cache DB triggers a full recompute, byte-identical to
  the original warm-cache report.
- TC-10 (CLI wiring reusability): the CLI warmer's published rows are 100% cache hits for a subsequent
  bare `run_strategy_comparison_report(sub_cache=<same path>)` call — zero fresh `_run_backtest` calls.
- TC-11 (manager resumability): `trigger()` completing once (via an injected sub_cache), then a
  partially-aborted overlapping run re-triggered with the SAME sub_cache, ends with
  `backtests_from_cache > 0` — proving `trigger()` genuinely threads a real cache, not the `None`
  default.
- TC-12 (no-parallelism-in-manager guard): a test asserts `trigger()` never supplies `workers > 1` to
  `run_strategy_comparison_report` (monkeypatch-captured kwargs).
- TC-13 (byte-identity of the hooked path): `sub_cache=None` vs a genuinely-warm `sub_cache` produce
  byte-identical reports for the same inputs.
- TC-14 (frozen foundations): full backend suite green; source-introspection guards + the MCP
  tool-count guard (18 tools) pass byte-unmodified; `config_fingerprint()` still `4d665603569b9dbf`;
  `levels.py`/`tradability.py`/`backtests.py`/`bars.py`/`datasets.py`/`dataset_index.py`/
  `app/mcp/__init__.py` git-confirmed byte-unchanged vs the pre-iteration tree.
- Required-still-passing J-01, J-02, J-03, J-07 remain green (replay + LLM fallback, mechanically
  verified in the same scoped browser pass used for TC-1/TC-2).
- Full unit suite green, no regressions, `config_fingerprint` unchanged, dev handoff written.

## Process Notes

- **Chrome MCP has failed to start in each of the last 2 iterations** (reproduced by 4+ independent
  agents in iter-4: "Chrome did not become ready on port 9222"). Retry the identical scoped recipe in a
  fresh session. Per the phase spec's own explicit fallback: if it STILL fails, this is NOT a blocker
  for J-05 — TC-4 through TC-14 are fully keyless/automated and must still be delivered and evaluated on
  their own evidence; J-04 stays `partial` (never regresses to `failing` for an infra reason) and the
  blocker is escalated to the operator again, exactly as iter-4 already flagged.
- A prior golden-replay "possible regression" FAIL must be checked against its own evidence screenshot
  before being trusted — a "Backend unreachable" render is an infra false-negative, not a regression
  (iter-4's own lesson, applies to any replay-lane finding against J-01/J-02/J-03/J-07 this iteration).
- The equivalence/byte-identity claims (TC-5, TC-8 especially) need non-vacuous proof — a spy showing
  the mutation/parallelism actually took effect, not just "the test passed" (iter-3's lesson, repeated
  verbatim in the phase spec's own NOTES).
