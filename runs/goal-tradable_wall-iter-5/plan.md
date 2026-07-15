# goal-tradable_wall-iter-5 Execution Plan

Backend-only enabler pass (depth: full). Resolves the two blocking watch-items the iter-4
evaluator named ("B1", "B3") that must be fixed **before** J-05 renders `/structure` in iter-6.
No journey flips this iteration (J-05 stays `failing` by design); measurable capability only.
Fully aligned with `docs/goal.md` (Era 5B) and the iter-4 evaluator's explicit next-step
recommendation — no scope drift, no contradiction with the goal doc found.

## What to Build

- **B1 — additive recency-boundary disclosure** in `apps/backend/app/research/setups.py`
  (`_reaction_and_forward_returns`, `_event`): when a touch event's reaction horizon is truncated
  at the last stored bar (`touch_index + horizons[0] >= len(all_bars)`), additively expose (a) the
  **effective reaction horizon actually used, in bars**, and (b) a boolean
  `reaction_boundary_truncated`. Do NOT mutate the existing `reaction` label, do NOT drop the
  event. Non-boundary events get `reaction_boundary_truncated: false` and the full configured
  `horizons[0]` as their effective horizon — byte-identical `reaction`/`forward_returns` to today.
- **B1 boundary regression test** — the committed AAPL 5m fixture
  (`tests/fixtures/yahoo/AAPL_5m_20260615_20260630.json`) stops 2026-06-30, i.e. before any
  boundary condition can occur, so it cannot exercise this path. Build a purpose-built
  synthetic multi-session fixture/shape (mirroring the existing `SYN-SETUPS-A` synthetic-fixture
  pattern already in `tests/test_setups.py`) whose final touch has fewer than
  `Config.setups_forward_return_horizons_bars[0]` (= 78) bars remaining in the store. Assert exact
  values: a definitive `reaction`, horizon-0 `forward_returns[0].return_fraction is None`,
  `reaction_boundary_truncated is True`, effective horizon `< 78`.
- **B1 non-boundary byte-identity test** — the pinned AAPL 2026-06-22 event stays `reaction:
  "rejected"`, forward returns `[-0.462%, -4.269%]`, `touch_ts 2026-06-22T13:30:00Z`, and
  `reaction_boundary_truncated: false` — byte-identical to pre-change output except the two new
  additive fields.
- **B3 — memoize the one full-panel `compute_setups` scan**, entirely internal to `setups.py`,
  behind a rebuildable, **process-local**, **store-content-keyed** cache (the same "rebuildable
  accelerator, never a source of truth" contract the existing `bar_index.py` cache lives under —
  but in-process only, never SQLite/disk-persisted). Key it on a deterministic signature over
  `BarStore.list()` (e.g. sorted `(symbol, timeframe, id, checksum)` tuples — `bars.py` already
  exposes a per-series `checksum` in every list record). `compute_setups(store, config)`'s own
  signature must NOT change, so `routes.py` (`list_setups` line ~1882, `get_setup` line ~1904) and
  `edge_report.py`'s call (line ~447) need **zero changes** — the memoization is invisible to
  every caller.
- **B3 tests**: (1) byte-identity — a cached read equals a fresh `compute_setups` call, checked
  through all three call sites; (2) computed-once-per-unchanged-store — a call-count spy via
  monkeypatch (mirror the existing precedent `test_compute_setups_runs_at_most_once_per_report_call`
  in `tests/test_edge_report.py`) proves the underlying scan runs exactly once across repeated
  reads, never per-request; (3) checksum-bust — appending a series to the store re-runs the scan
  and never serves a stale result; (4) immutable-safety — a `/setups/{id}` enriched read (which
  calls `enrich_with_tape_timeline`, already copy-on-write per its docstring) followed by a
  `/setups` list read returns the un-enriched list verbatim — the shared cached object must never
  be mutated by a caller.
- **J-03 keyless enrichment stays unbroken** — `GET /research/setups/{id}` still returns the exact
  joined `tape_timeline` over the committed `tests/fixtures/datasets_j03/` fixture after the cache
  lands (re-run the existing join tests; add one that exercises the cache path explicitly if not
  already covered).
- **Frozen byte-identity re-verification** (do not implement — verify and cite in the handoff):
  `config_fingerprint() == 4d665603569b9dbf`; strategy registry order stays
  `(v1, structure_tape, structure_tape_map)`; `git diff --name-only -- apps/` touches only
  `setups.py` (+ its own tests, + a small owned cache helper if factored out) — `levels.py`,
  `tradability.py`, `engine/`, `strategies.py`, `bars.py`, `datasets.py`, `adapters/`,
  `edge_report.py`, and `backtests.py` (existing outputs) must be absent from the diff.
- Full backend suite green (`cd apps/backend && .venv/bin/python -m pytest tests/ -q`); replay
  J-01, J-02, J-04, J-07 deterministically (no regressions).
- Dev handoff at `docs/handoffs/goal-tradable_wall-iter-5-dev.md`.

**Not building this iteration** (explicit OUT OF SCOPE in the phase spec — do not touch): the
`/structure` frontend render (J-05, deferred to iter-6), any cockpit change (J-06, iter-7), the
credentialed ≥10-window recording (J-03's remaining credentialed portion, operator-gated), any
change to the `reaction` *value* of a non-boundary event or exclusion of boundary events, any
change to frozen files/outputs or the config fingerprint/champion pointer, disk-persisting the
cache, or any new MCP tool.

**Blueprint note:** `runs/goal-session-tradable_wall/state/blueprint.md` already carries the
iter-5 additive note on the existing "Touch events..." Data-Contract row (added by the
goal-decomposer) — no new row, no nav change, no further blueprint edit needed. The implementation
must match that description exactly: single computer (`setups.py`), rebuildable accelerator never
a source of truth, byte-identical cached-vs-fresh output.

## Agents Required
- backend-data: yes -- implement B1 (recency-boundary disclosure) + B3 (memoized scan cache) in
  `apps/backend/app/research/setups.py`, all listed tests, and the frozen-byte-identity
  re-verification; write the dev handoff.
- frontend-ux: no

Frontend Present: no

## Files to Create/Modify
- `apps/backend/app/research/setups.py` -- B1 additive fields in `_reaction_and_forward_returns`/
  `_event`; B3 internal memoization wrapper around the existing scan body of `compute_setups`.
- `apps/backend/tests/test_setups.py` -- B1 boundary regression test (new purpose-built fixture),
  B1 non-boundary byte-identity test (pinned AAPL), B3 cache tests (byte-identity, computed-once,
  checksum-bust, immutable-safety), J-03 enrichment-after-cache re-check.
- `apps/backend/tests/test_setups_api.py` -- re-verify `list_setups`/`get_setup` route behavior is
  unaffected (byte-identical shape plus the two new additive fields); confirm no route code
  changed.
- `apps/backend/tests/test_edge_report.py` -- re-verify `run_strategy_comparison_report` still
  calls `compute_setups` exactly once per report and gets cache-backed results transparently.
- `apps/backend/tests/fixtures/` -- possible new small purpose-built fixture file for the B1
  boundary test, if a static fixture (rather than an in-test-constructed shape) is used.
- `docs/handoffs/goal-tradable_wall-iter-5-dev.md` -- dev handoff (new).

No frontend files. No changes anywhere outside `apps/backend/app/research/setups.py` and its
tests are expected.

## Key Test Scenarios
- Boundary event: definitive `reaction`, horizon-0 `forward_returns[0].return_fraction is None`,
  `reaction_boundary_truncated is True`, effective horizon strictly less than
  `Config.setups_forward_return_horizons_bars[0]`.
- Non-boundary pinned AAPL 2026-06-22 event: `reaction == "rejected"`, forward returns
  `[-0.462%, -4.269%]`, `reaction_boundary_truncated is False`, effective horizon == 78 — otherwise
  byte-identical to pre-change output.
- Cache byte-identity: cached result of each of `/research/setups`, `/research/setups/{id}`,
  `edge_report.run_strategy_comparison_report`'s internal call equals a fresh (uncached)
  `compute_setups` call.
- Cache computed-once: a call-count spy shows the underlying scan body runs exactly once across N
  repeated reads against an unchanged store.
- Cache checksum-bust: appending a new bar series to the store causes the next read to re-scan
  (not serve stale data).
- Cache immutable-safety: `/setups/{id}` (enriched) then `/setups` (list) never leaks the
  enrichment into the list's events.
- `config_fingerprint() == "4d665603569b9dbf"`; registry order `(v1, structure_tape,
  structure_tape_map)`; diff-scope check shows only `setups.py` + tests changed.
- Full backend suite green; zero regressions in J-01/J-02/J-04/J-07 replay.
