# goal-desk-iter-3 Functional Test Plan

**Phase:** goal-desk-iter-3
**Date:** 2026-07-25
**Frontend Present:** no

## Phase Goal

An operator (or the CLI) can trigger a deterministic, append-only "screen" — one pass over the latest registered universe snapshot, as-of a given screen date, that summarizes each member's canonical tradable-map structure into a ranked row (or an honest skip) — and read it back byte-identical on every re-run, with zero new `Config` fields and zero diff on any frozen research module.

## Test Cases

### TC-01 — AAPL Row Byte-Identity to GET /research/tradability

**Type:** api
**Preconditions:** The committed fixture universe (103 members) is loaded; the real AAPL fixture bars for 2026-06-22 are available in the test temp bar dir; no prior screen has been computed.

**Steps:**
1. Trigger a screen computation via `POST /research/desk/screen/compute` with `{"screen_date": "2026-06-22"}`.
2. Poll `GET /research/desk/screen/compute` until `state` is `"done"`.
3. Retrieve the persisted screen via `GET /research/desk/screen?date=2026-06-22`.
4. Extract AAPL's row from the `rows` array.
5. Call `GET /research/tradability?symbol=AAPL&as_of=<the as_of value derived by desk_screen.py>` and extract the band that desk_screen.py selected as AAPL's "best" (per the selection rule: class rank A=3/B=2/C=1/null=0 desc, distance_bps asc, quality_score desc).
6. Compare AAPL row's `band_class`, `distance_bps`, `band_score`, `price_low`, `price_high` to the tradability endpoint's selected band's values.

**Expected outcome:** The values are byte-identical; AAPL's `distance_bps` is computed from the ONE daily bar dated at `basis_as_of` (confirmed via fixture inspection) and equals `abs(edge_price - close) / close * 10000`.

**Pass criteria:** HTTP 200 on all GET/POST calls; AAPL row present in `rows`; all five numeric/string fields match tradability endpoint exactly (byte-equal JSON).

---

### TC-02 — MSFT Partial Coverage Resolves as Ranked Row

**Type:** api
**Preconditions:** The committed fixture universe is loaded; a new MSFT bar fixture (covering `1h` and `1d` only, not `4h` or `1w`) is present in the test temp bar dir; no prior screen has been computed.

**Steps:**
1. Trigger a screen computation via `POST /research/desk/screen/compute` with `{"screen_date": "2026-06-22"}`.
2. Poll until `state` is `"done"`.
3. Retrieve the persisted screen via `GET /research/desk/screen?date=2026-06-22`.
4. Search the `rows` array for MSFT.
5. Inspect MSFT's `coverage` field and verify `1h.has_bars: true`, `1d.has_bars: true`, `4h.has_bars: false`, `1w.has_bars: false`.

**Expected outcome:** MSFT appears in `rows` (never mis-skipped for partial pinned-timeframe coverage); its coverage field honestly reports which timeframes have bars.

**Pass criteria:** MSFT row present in `rows`; `coverage` field has exactly four keys (`1h`, `1d`, `4h`, `1w`) with correct `has_bars` boolean per fixture shape; `symbol: "MSFT"`.

---

### TC-03 — Zero-Bar Members Appear in Skipped with "no_bars" Reason

**Type:** api
**Preconditions:** The committed fixture universe (103 members) is loaded; approximately 100 members have zero recorded bars on any timeframe; screen has not yet been computed.

**Steps:**
1. Trigger a screen computation via `POST /research/desk/screen/compute` with `{"screen_date": "2026-06-22"}`.
2. Poll until `state` is `"done"`.
3. Retrieve the persisted screen via `GET /research/desk/screen?date=2026-06-22`.
4. Count the entries in the `skipped` array where `reason: "no_bars"`.
5. Verify none of these symbols appear in the `rows` array.

**Expected outcome:** All zero-bar members are in `skipped`, not `rows`; every skipped entry with `reason: "no_bars"` is structurally sound.

**Pass criteria:** `skipped` count ≥ ~100; every entry has `skipped: true`, `reason: "no_bars"`, `symbol` present, `coverage` object present; zero overlap with `rows` array symbols.

---

### TC-04 — Identical Screen Date and Pins Refuse Recompute, Return Existing Snapshot

**Type:** api
**Preconditions:** A screen has already been computed and persisted for `screen_date=2026-06-22` under a known universe/bar-store state (fingerprint, bar_store_signature pinned).

**Steps:**
1. Retrieve the existing screen's `id` via `GET /research/desk/screen?date=2026-06-22`.
2. Trigger a second screen computation with identical `{"screen_date": "2026-06-22"}` via `POST /research/desk/screen/compute`.
3. Observe the response.
4. Poll `GET /research/desk/screen/compute` until terminal.
5. Retrieve the screen again via `GET /research/desk/screen?date=2026-06-22`.

**Expected outcome:** The manager returns the EXISTING snapshot (same `id`) without writing a second file; recomputing the row content in isolation produces byte-identical results to the first run.

**Pass criteria:** Response to second POST has `started: false`; returned snapshot `id` matches the first run's `id`; HTTP 200 and file count unchanged after the second trigger; direct recomputation is byte-equal.

---

### TC-05 — GET /research/desk/screen with No Prior Compute Returns Empty List

**Type:** api
**Preconditions:** The test environment has a fresh temp screen dir with no prior screen snapshots.

**Steps:**
1. Call `GET /research/desk/screen` (no query params).

**Expected outcome:** HTTP 200 with `{"screens": [], "latest": null}`.

**Pass criteria:** Response status 200; response body is exactly `{"screens": [], "latest": null}` (never 404, never a fabricated row).

---

### TC-06 — GET with Date Query Returns Persisted Snapshot Verbatim

**Type:** api
**Preconditions:** A screen has been computed and persisted for `screen_date=2026-06-22`.

**Steps:**
1. Retrieve the persisted screen via `GET /research/desk/screen?date=2026-06-22`.
2. Record the `rows` and `skipped` arrays exactly as returned.
3. Call `GET /research/desk/screen?date=2026-06-22` again.
4. Compare the two responses byte-for-byte.

**Expected outcome:** The GET endpoint returns the persisted snapshot verbatim on every call; the snapshot is never recomputed on GET.

**Pass criteria:** HTTP 200; both GET calls return identical JSON (byte-equal `rows` and `skipped` arrays); response timestamp `created_utc` matches the original compute time.

---

### TC-07 — Concurrent Trigger While Running Returns Same Job

**Type:** api
**Preconditions:** A screen compute is triggered and confirmed in-flight (state `"running"` via `GET /research/desk/screen/compute`).

**Steps:**
1. Trigger the screen computation with a DIFFERENT screen_date (or same date, but ensure the first is still running): `POST /research/desk/screen/compute` with `{"screen_date": "2026-06-20"}` (different from in-flight).
2. Immediately poll `GET /research/desk/screen/compute` while the first job is still running.
3. Verify the response to the second trigger.

**Expected outcome:** The second trigger for a DIFFERENT date starts a new job; if the second trigger is for the SAME date as an in-flight job, the response reports `started: false` and returns the SAME job unchanged (single-flight per date).

**Pass criteria:** Response has `started: false` and `compute` object matches the in-flight job's snapshot (same `id`, `screen_date`, `started_utc`); HTTP 200.

---

### TC-08 — Cancel Mid-Flight Transitions to Cancelled; Idle Cancel Returns 409

**Type:** api
**Preconditions:** A screen compute is in-flight (state `"running"`).

**Steps:**
1. Call `POST /research/desk/screen/compute/cancel` while the job is running.
2. Poll `GET /research/desk/screen/compute` immediately and observe the state transition.
3. Record `members_total` and `members_done` at cancellation.
4. In a separate test, trigger cancel when no job has ever run (or all prior jobs are terminal).
5. Observe the response.

**Expected outcome:** Cancel mid-flight transitions the state to `"cancelled"` with `finished_utc` set; `members_done` is fewer than `members_total`. Idle cancel returns HTTP 409.

**Pass criteria:** Mid-flight cancel: HTTP 200, state `"cancelled"`, `finished_utc` is ISO timestamp, `members_done < members_total`. Idle cancel: HTTP 409.

---

### TC-09 — Compute Trigger with Missing screen_date Returns 422

**Type:** api
**Preconditions:** The compute endpoint is reachable.

**Steps:**
1. Call `POST /research/desk/screen/compute` with an empty body `{}`.
2. Call again with `{"other_field": "value"}` (no `screen_date`).

**Expected outcome:** Both calls are rejected with HTTP 422; the endpoint never defaults to today's wall-clock date.

**Pass criteria:** HTTP 422 on both malformed requests; response includes an error message indicating missing `screen_date`; no compute job is triggered.

---

### TC-10 — Byte-Identical Computation Across Fresh Test Processes

**Type:** api
**Preconditions:** Two independent test processes, each with a fresh temp universe/bar/screen dir; both load the committed fixture universe and real bar fixtures.

**Steps:**
1. In process A, trigger a screen computation for `screen_date=2026-06-22` via `POST /research/desk/screen/compute`.
2. Poll until done and retrieve the result via `GET /research/desk/screen?date=2026-06-22`.
3. In process B (with a different temp dir but same fixture data), trigger an identical screen computation for the same date.
4. Poll until done and retrieve the result.
5. Compare the two snapshots' `rows` and `skipped` arrays byte-for-byte.

**Expected outcome:** Both processes produce byte-identical results (no wall-clock, no unseeded randomness anywhere in the computation).

**Pass criteria:** JSON of `rows` and `skipped` arrays are byte-equal; both have identical `id`, `bar_store_signature`, `config_fingerprint`.

---

### TC-11 — Symbol with Daily Series but No Resolvable Basis Appears in Skipped with "no_basis"

**Type:** api
**Preconditions:** A symbol exists in the fixture universe with at least a daily bar series, but `compute_tradability` cannot resolve a prior session (`no_bar_series_for_symbol: false`, but `basis_as_of: null`).

**Steps:**
1. Trigger a screen computation via `POST /research/desk/screen/compute` with `{"screen_date": "2026-06-22"}`.
2. Poll until done.
3. Retrieve the screen via `GET /research/desk/screen?date=2026-06-22`.
4. Search the `skipped` array for entries with `reason: "no_basis"`.
5. Verify the symbol is NOT in the `rows` array.
6. Inspect the skipped row's `coverage` field to confirm it still reports which timeframes have bars.

**Expected outcome:** The symbol appears in `skipped` with `reason: "no_basis"` (distinct from `"no_bars"`); its `coverage` field honestly reflects which pinned timeframes DO have bars (never all-false when bars genuinely exist).

**Pass criteria:** Skipped row has `skipped: true`, `reason: "no_basis"`, `coverage` object with at least one timeframe showing `has_bars: true` or `has_bars: false` per actual fixture state; symbol not in `rows`.

---

### TC-12 — Coverage Field Byte-Identical to desk_coverage.get_desk_coverage

**Type:** api
**Preconditions:** A screen has been computed and persisted; `desk_coverage.get_desk_coverage` is callable on the same universe snapshot.

**Steps:**
1. Retrieve the screen via `GET /research/desk/screen?date=2026-06-22`.
2. For each member in `rows` and `skipped`, extract its `coverage` field.
3. Call `desk_coverage.get_desk_coverage(universe_snapshot, symbol)` for the same universe snapshot (using `universe_snapshot_id` from the screen).
4. Compare each member's `coverage` to the corresponding result from `get_desk_coverage`.

**Expected outcome:** Every row's (ranked or skipped) `coverage` field is byte-identical to `desk_coverage.get_desk_coverage`'s own per-member `per_timeframe` block, proving reuse, not re-derivation.

**Pass criteria:** For each symbol in screen, its coverage JSON matches `get_desk_coverage`'s return exactly; structure and all boolean/string values are identical.

---

### TC-13 — Tick Evidence Flag Per Dataset Registration

**Type:** api
**Preconditions:** The 11 named dataset-store symbols (AAPL, AMD, AMZN, GOOGL, META, MSFT, NFLX, NVDA, PG, SPY, TSLA) are registered in the temp dataset store; a screen has been computed.

**Steps:**
1. Retrieve the screen via `GET /research/desk/screen?date=2026-06-22`.
2. For each member in `rows` and `skipped`, check its `tick_evidence` flag.
3. Cross-reference the symbol against the 11 registered dataset symbols.

**Expected outcome:** The 11 named symbols have `tick_evidence: true`; every other member has `tick_evidence: false`.

**Pass criteria:** All 11 named symbols in screen (whether in `rows` or `skipped`) show `tick_evidence: true`; all other members show `tick_evidence: false`.

---

### TC-14 — Rows Sorted by Deterministic Tuple (Band Class, Distance BPS, Band Score, Symbol)

**Type:** api
**Preconditions:** A screen has been computed with at least two distinct resolved band classes among its ranked rows.

**Steps:**
1. Retrieve the screen via `GET /research/desk/screen?date=2026-06-22`.
2. Extract the `rows` array.
3. Verify the sort order manually: iterate `rows` and confirm each entry satisfies the ordering rule: `(band_class rank A>B>C>null desc, distance_bps ascending, band_score descending, symbol ascending)`.

**Expected outcome:** The `rows` array is sorted exactly by the tuple; no row violates the order.

**Pass criteria:** For each consecutive pair of rows, the ordering invariant holds (no inversions); spot-check: A-class rows come before B-class; within the same class, lower distance_bps comes first.

---

### TC-15 — Bar Store Signature Sourced Entirely from bar_index, Zero BarStore File Reads

**Type:** api
**Preconditions:** A screen is being computed; instrumentation is in place to count `BarStore.list` and `BarStore.get` calls.

**Steps:**
1. Trigger a screen computation via `POST /research/desk/screen/compute` with `{"screen_date": "2026-06-22"}`.
2. Instrument the code to track calls to `BarStore.list()` and `BarStore.get()` during `bar_store_signature` derivation.
3. Poll until done.
4. Verify the call count.

**Expected outcome:** The `bar_store_signature` derivation issues zero `BarStore.list` or `BarStore.get` calls; it is sourced entirely from `desk_coverage.get_desk_coverage`'s own reads (already index-backed, already proven index-fast in J-02).

**Pass criteria:** Call count for `BarStore.list` during signature derivation = 0; call count for `BarStore.get` = 0; `bar_store_signature` is present in the persisted snapshot and non-empty.

---

### TC-16 — Config Fingerprint Unchanged at 08e471b10130e1e2

**Type:** artifact
**Preconditions:** The codebase state before the iteration's changes; the codebase state after all iteration changes.

**Steps:**
1. Before running any tests: call `Config().config_fingerprint()` and record the value.
2. Run all unit/integration tests and complete the iteration.
3. After all changes: call `Config().config_fingerprint()` again and record the value.

**Expected outcome:** The fingerprint is unchanged at `08e471b10130e1e2` (zero new `Config` fields are added).

**Pass criteria:** Both values are identical: `08e471b10130e1e2`; git diff on `config.py` is empty.

---

### TC-17 — Suite Passes >= 1240 / 8 Skipped; Guard Tests Pass Byte-Unmodified

**Type:** api
**Preconditions:** All iteration code is complete; the full backend suite is ready to run.

**Steps:**
1. Run the full backend test suite.
2. Record exact pass/skip/fail counts.
3. Run all guard tests: `test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, and the 13 fingerprint pin assertions.
4. Verify every guard test passes.

**Expected outcome:** Suite passes with a count >= 1240 passed / >= 8 skipped / 0 failed (iter-2's floor); every guard test passes byte-unmodified.

**Pass criteria:** Final count shows ≥1240 passed, ≥8 skipped, 0 failed; all guard tests exit with status 0; no new or modified guard test assertions fail.

---

### TC-18 — CLI Requires --date Argument; Rejects No-Arg Invocation

**Type:** api
**Preconditions:** The CLI warmer (e.g., `python -m app.research.desk_screen_compute`) is available.

**Steps:**
1. Invoke the CLI with no arguments: `python -m app.research.desk_screen_compute`.
2. Observe the exit code and error message.
3. Invoke the CLI with `--date 2026-06-22` against a scoped test/fixture dir (setting `TAPEOLOGY_DESK_UNIVERSE_DIR`, `TAPEOLOGY_BAR_DIR`, `TAPEOLOGY_DESK_SCREEN_DIR`).
4. Observe completion and output.

**Expected outcome:** No-arg invocation exits non-zero with explicit usage error (never silently using today's date); `--date 2026-06-22` runs to completion and prints a ranked/skipped summary count.

**Pass criteria:** No-arg exit code ≠ 0; error message mentions `--date` or "required"; `--date` invocation exits with code 0; output includes a summary line with counts.

---

### TC-19 — Distance BPS Uses Basis Bar's Close; tradability.py and levels.py Untouched

**Type:** api
**Preconditions:** The real AAPL fixture bars and the screen computation are available; `tradability.py` and `levels.py` are in their original state.

**Steps:**
1. Retrieve a screen row for AAPL with a resolved "best" band.
2. Extract the `basis_as_of` value from the `compute_tradability` result for AAPL (via direct function call or from screen metadata).
3. Look up the ONE daily bar dated at `basis_as_of` in the real AAPL fixture.
4. Read the close price from that bar.
5. Verify AAPL row's `distance_bps` equals `abs(edge_price - close) / close * 10000`, where `edge_price` is the "best" band's `price_low` (for resistance) or `price_high` (for support).
6. Run `git diff tradability.py` and `git diff levels.py`.

**Expected outcome:** The reference close price is correctly read from the fixture bar at `basis_as_of`; `distance_bps` computation is correct; `git diff` on both files is empty (no changes to return shapes or existing methods).

**Pass criteria:** Manual calculation matches the returned `distance_bps` value (within floating-point tolerance); `git diff tradability.py` output is empty; `git diff levels.py` output is empty.

---

## Summary

**Total test cases:** 19

**By type:**
- API tests: 18 (TC-01 through TC-15, TC-17 through TC-18)
- Artifact checks: 1 (TC-16)

**By focus area:**
- Store discipline (append-only, checksum, integrity): TC-04, TC-05, TC-06, TC-10, TC-16
- Row computation (rank, skip reasons, cross-module consistency): TC-01, TC-02, TC-03, TC-11, TC-12, TC-14, TC-19
- Compute manager (single-flight, cancel, progress): TC-07, TC-08, TC-09
- Routes and CLI: TC-18
- Fingerprint pin and guard tests: TC-16, TC-17
- Performance (bar-store signature indexing): TC-15
- Determinism (byte-identical re-runs): TC-10, TC-14

All test cases reference the committed fixture universe (103 members) and real bar fixtures (AAPL, new MSFT partial-coverage). No synthetic AAA…EEE stand-ins are used for symbol-specific tests.
