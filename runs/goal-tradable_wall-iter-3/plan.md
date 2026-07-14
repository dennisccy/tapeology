# goal-tradable_wall-iter-3 Execution Plan

**Journey:** J-03 — tape-at-the-wall: the keyless recording + engine-replay join substrate.
**Required-still-passing:** J-01, J-02, J-07 (frozen-foundation sentinel).

## Alignment with docs/goal.md

Directly serves Key Capability #3 ("Event-windowed real tape recording") and #4 ("Tape-at-the-wall
join") and Must-have journey J-03. Dependency order (J-01 -> J-02 -> **J-03** -> J-04) is respected;
nothing here front-runs J-04 (edge report/`structure_tape_map`), J-05 (`/structure` UI), or J-06
(cockpit chip) — all correctly OUT OF SCOPE per the phase spec. No drift from the goal found: the
spec's "keyless substrate now, credentialed headline honestly blocked" framing matches the
`ALPACA_API_KEY`/`ALPACA_API_SECRET`/`TAPEOLOGY_LIVE_INTEGRATION` triple being **confirmed absent**
in this environment (re-verified directly: zero matches in `env`). Expect this iteration to land
`partial`, not full `passing` — that is the DoD's own stated expectation, not a shortfall.

## What to Build

- **Event-window recording driver** — a new operator script mirroring `scripts/populate_panel_bars.py`'s
  precedent (in-process `TestClient`, drives the *existing* route, no new production HTTP path):
  selects top-ranked events from `compute_setups`/`GET /research/setups`, always includes the pinned
  AAPL 2026-06-22 ~300 event, and records each event's window (touch −60min…+90min, config-owned
  padding) via `POST /research/datasets` (`source_kind="historical"`), which is **already wired**
  end-to-end to the Alpaca adapter (see Architecture Facts below) — no new recording plumbing needed.
- **Tape-at-the-wall join** onto `GET /research/setups/{id}`: replay a matched recorded dataset
  through the frozen `TapeEngine` (via `DatasetStore.replay`, which already exists) and attach the
  five-state timeline to the drill-in's `tape_timeline` field (currently hardcoded `[]`).
- **ONE new committed tick-fixture slice** under `apps/backend/tests/fixtures/` so the join path is
  CI-tested keyless.
- **Config-owned constants** (padding, event-selection cap, a NEW deterministic split-assignment
  rule — see Architecture Facts, this rule does not exist yet) added to the `config_fingerprint`
  exclusion set (`tradability_*`/`setups_*` precedent).
- **Tests**: join-path exact-state/order assertions, `DatasetStore` immutable-data discipline,
  feed-stamp-verbatim, single-source-of-truth guard (setups.py never reimplements the state machine),
  frozen-foundation byte-identity + fingerprint, no-credential-in-artifacts grep, and an
  `integration`-marked credentialed test that honestly SKIPS here (keys absent).
- **Dev handoff** at `docs/handoffs/goal-tradable_wall-iter-3-dev.md`, explicitly stating the
  credentialed recording ran or was blocked.

## Agents Required

- backend-data: yes -- all of the above (recording driver script, `setups.py` join function, config
  constants, routes.py wiring, fixture, and the full test suite described above).
- frontend-ux: no -- zero UI/frontend files this iteration; the drill-in's tape timeline is rendered
  by J-05, not J-03. Verification is by backend tests + API reproduction only (the same discipline
  backend-only J-01/J-02 already used).

Frontend Present: no

## Architecture Facts (verified in the codebase — read before implementing; each saves real investigation time)

1. **The credentialed recording path is ALREADY wired end-to-end.** `POST /research/datasets` with
   `source_kind="historical"` (`app/research/routes.py:1467-1480`) already resolves the adapter via
   `get_study_market_adapter()` and builds `historical_fetch` via the existing `_build_historical_fetch`
   helper (`routes.py:1237`), which calls `adapter.fetch_historical(symbol, start, end)` — the exact
   same seam era-3's studies runner uses. The recording driver script does **not** need to touch the
   Alpaca adapter or build a new fetch seam: it just POSTs to this existing route (or calls
   `record_from_source` in-process with the same `historical_fetch` builder), exactly as
   `populate_panel_bars.py` drives `POST /research/bars`. When credentials are absent,
   `adapter.is_available()` is `False` and the route returns an explicit 422 — the script should count
   and honestly report this as "blocked," mirroring `populate_panel_bars.py`'s existing SKIP/FAIL
   counters (never fixture-substitute).
2. **`DatasetStore.replay(dataset_id, config)` already exists** (`app/research/datasets.py:268`) and
   yields an `Iterator[EngineSnapshot]` by replaying the stored dataset through a **fresh** `TapeEngine`
   — this is the entire "replay through the frozen engine" mechanism; nothing new needs to be built
   for that part of the join, only consumed.
3. **`DatasetStore`'s meta schema is FROZEN and has no "associated event" field** (`record()`'s
   keyword args are fixed: symbol/source/source_kind/source_id/split/window_start_utc/window_end_utc/
   data_feed/epoch_anchor/events — confirmed by direct read, and OUT OF SCOPE explicitly forbids
   changing `DatasetStore` internals). **The join must therefore match a setups event to a recorded
   dataset by `symbol` equality + the dataset's `[window_start_utc, window_end_utc]` containing the
   event's `touch_ts`** — not by a new id field. Pick a deterministic tie-break (e.g. earliest
   `created_utc`) for the rare case more than one dataset window covers the same touch.
4. **The join belongs in a new `setups.py` function, called ONLY from `get_setup`
   (`routes.py:1891`, the `/{id}` detail route) — never inside `compute_setups()`'s per-session scan
   loop.** `compute_setups()` is shared by both `list_setups` and `get_setup`; adding a per-event
   `DatasetStore` lookup inside its loop would add O(events) dataset-store scans to the already-slow
   ~4m43s full-panel list route (audit B2, carried, not this iteration's to fix) and risks entangling
   the join with the B1 boundary-label issue (explicitly NOT this iteration's scope). Keep
   `compute_setups()`'s output byte-identical; enrich only the single looked-up event inside
   `get_setup`, which needs a second dependency: `dataset_store: DatasetStore = Depends(get_dataset_store)`
   (that dependency function already exists at `routes.py:1408`, trivially reusable).
5. **A transition-collapsing precedent already exists**: `HistoryBuffer.note_state`
   (`app/engine/history.py:109`) appends a marker only when `tape_state` CHANGES ("states + transition
   times", not one row per raw tick). The join's timeline construction should mirror this idiom
   (iterate the `replay()` snapshot stream, emit an entry only on a state change) rather than emit one
   row per event. Whether to include transitions into `unclear` (the `note_state` precedent excludes
   it) is open — no spec bullet forces either way; pick one and document the reasoning.
6. **No pre-existing "seeded split rule" was found** despite the DoD phrase "reusing the existing
   seeded split rule" (grep across `app/` and `tests/` for seeded/deterministic split-assignment logic
   returned nothing). Read this as "reuse the EXISTING split *mechanism*" (the `SPLIT_TRAIN`/
   `SPLIT_HOLDOUT` vocabulary and `record_from_source(split=...)` parameter already in
   `datasets.py`) while **designing a NEW, config-owned deterministic assignment rule** this iteration
   — e.g. a pure function of each event's own stable identity (the codebase's own sha256-digest idiom,
   already used for event ids in `setups.py:211`) checked against a config-owned train/holdout ratio.
   Do not spend time hunting for a rule that already exists — it doesn't.
7. **Hermetic historical-source test pattern already exists**: `tests/test_datasets_api.py` overrides
   `app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(window=...)` and POSTs
   `source_kind="historical"` — fully keyless. The new committed tick-fixture's join-path test should
   follow this exact pattern (or call `record_from_source(..., historical_fetch=lambda: window)`
   directly, as `test_datasets.py` already does for its own reference-window tests) rather than
   inventing a new hermetic-injection mechanism.
8. **`@pytest.mark.integration` + `TAPEOLOGY_LIVE_INTEGRATION` skip-gate precedent**:
   `tests/test_live_integration.py` is the exact pattern to mirror for the new credentialed recording
   test (check the env flag, then `adapter.is_available()`, `pytest.skip(...)` with a clear reason —
   never silently pass). That file is Alpaca **live-socket** specific; the new test (historical
   fetch/record, not streaming) should live in its own file.
9. **`config_fingerprint`'s exclusion set is a plain Python `set` literal** at
   `app/config.py:1582` inside the `config_fingerprint()` method (the `tradability_*`/`setups_*`
   precedent from iter-1/iter-2 lives in this same set). Add the new padding/cap/split-rule constants
   there with a rationale comment in the same style.
10. **No new endpoint and no new MCP proxy** — `GET /research/datasets`, `GET /research/datasets/{id}`,
    `GET /research/setups`, `GET /research/setups/{id}` and their MCP proxies (`datasets`, `setups`)
    already exist and are reused verbatim; this iteration only enriches what `get_setup` returns.
11. **`test_no_execution_path.py` is the structural precedent for a repo-wide grep gate** (compound
    identifiers, proven non-vacuous, proven signal-bearing via a seeded counter-example) — but note it
    *excludes* `fixtures/` from its scan. The new no-credential-in-artifacts grep test needs the
    **opposite** scope: it must explicitly **include** fixtures, logs, and reports (the DoD says "any
    source file, fixture, log, test artifact, or report") — do not copy the exclusion list verbatim.

## Files to Create/Modify

- `apps/backend/scripts/record_event_windows.py` (NEW, naming suggestion) -- the recording driver
  operator script (`populate_panel_bars.py` precedent).
- `apps/backend/app/research/setups.py` (MODIFY) -- add the tape-timeline join function (matches
  event to dataset by symbol + window containment; replays via `DatasetStore.replay`; collapses to
  state transitions). Does NOT touch `compute_setups()`'s scan loop.
- `apps/backend/app/research/routes.py` (MODIFY) -- `get_setup` gains a `DatasetStore` dependency and
  calls the new join function before returning.
- `apps/backend/app/config.py` (MODIFY) -- new config constants (recording padding, event-selection
  cap, split-assignment ratio/rule) + their `config_fingerprint` exclusion-set entries.
- `apps/backend/tests/fixtures/<new tick fixture>.json` (NEW) -- one short recorded-event-window
  slice, honestly feed-stamped, may reuse/slice an existing committed fixture.
- `apps/backend/tests/test_setups.py` / `test_setups_api.py` (MODIFY) -- join-path + single-source-
  of-truth-guard tests.
- `apps/backend/tests/test_datasets.py` / `test_datasets_api.py` (MODIFY, if needed) -- any additional
  `DatasetStore` discipline coverage specific to the recording driver's usage pattern.
- New test file(s) for: no-credential-in-artifacts grep gate, and the `integration`-marked credentialed
  recording test (mirrors `test_live_integration.py`'s gating, historical-fetch flavor).
- `docs/handoffs/goal-tradable_wall-iter-3-dev.md` (NEW) -- dev handoff.

## Key Test Scenarios

- Join path: seed one dataset (keyless, via the `FakeAdapter`/direct-`historical_fetch` pattern) whose
  window covers a known event's touch; `GET /research/setups/{id}` returns a non-empty, correctly-
  ordered five-state timeline; a non-recorded event's `tape_timeline` stays `[]`.
- `DatasetStore` discipline: append-only, checksum-verified, `feed` stamped verbatim, split frozen at
  registration (re-registration refused) — via the recording driver's own usage.
- Static/behavioral guard: `setups.py`'s join function calls the frozen `TapeEngine`/`DatasetStore.replay`
  and never reimplements a tape state (mirrors the iter-2 "never a second map engine" guard).
- Frozen-foundation byte-identity: `TapeEngine`, `record_from_source`/`DatasetStore`, Alpaca adapter
  absent from the diff; `config_fingerprint == 4d665603569b9dbf`; new constants in the exclusion set.
- No-credential-in-artifacts grep test over source, fixtures, logs, and reports (new test, no literal
  Alpaca key/secret anywhere).
- `integration`-marked credentialed test: skips honestly here (keys absent) — this is the CORRECT,
  expected outcome in this environment, not a bug for review/QA to flag as a failure.
- Required-still-passing: full backend suite green; J-01/J-02/J-07 re-verified (fingerprint, frozen
  files diff-absent, `GET /research/setups`/`/{id}` contract still serves J-02's registry verbatim).
- Error cases: empty recording window -> existing `EmptyWindowError`; missing credentials -> the
  existing adapter-unavailable 422 (honestly blocked, never substituted); unknown `setup_id` -> 404
  (already exists); malformed padding/selection/split config -> rejected at config load.

## Notes for Reviewer / QA / Auditor

- **Frontend Present: no** — no Chrome MCP browser checks required; verify by backend tests + direct
  `GET /research/setups/{id}` API reproduction, as J-01/J-02 were verified.
- **The ≥10-window/≥5-symbol credentialed acceptance headline is EXPECTED to be honestly `blocked`**
  in this environment (Alpaca env vars confirmed absent by direct check). Do not treat this as a
  failed DoD item — the spec explicitly scopes this iteration to ship the keyless substrate and
  documents the credentialed step as operator-gated. Confirm the dev handoff states this explicitly
  rather than silently omitting it.
- Watch for scope creep into J-04 (edge report / `structure_tape_map`) or J-05 (`/structure` UI) —
  neither should appear in this iteration's diff.
- Confirm the join function was added ONLY to the `/{id}` detail path, not to `compute_setups()`'s
  shared scan loop (a regression risk for J-02's list-route performance/behavior).
