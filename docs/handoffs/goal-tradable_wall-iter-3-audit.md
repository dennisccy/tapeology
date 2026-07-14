# goal-tradable_wall-iter-3 Audit Report

**Date:** 2026-07-14
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase's actual deliverable — the **keyless tape-at-the-wall join substrate** — is truly complete and correct: `enrich_with_tape_timeline` replays a matched `DatasetStore` window through the FROZEN `TapeEngine` via `DatasetStore.replay` (never reimplemented), is wired ONLY into `GET /research/setups/{id}`, leaves `compute_setups`/`list_setups` byte-identical, keeps `config_fingerprint == 4d665603569b9dbf`, ships one honestly `sip`-stamped committed fixture, and is proven by tight exact-value tests with zero regressions and zero credential leakage (verified by a repo-wide grep for the real key/secret = 0 hits). The one GAP is the **credentialed ≥10-window headline**, which the handoff/QA/summary frame as "MET" but which is honestly `partial`/`unknown`: the integration run was interrupted before capturing a pytest PASS, the pinned-AAPL drill-in five-state timeline was never demonstrated end-to-end (only a JPM proxy), and the 15 datasets lived in an ephemeral pytest temp dir that does not persist — the spec, however, makes that headline explicitly operator-gated ("keeps J-03 short of full passing"), so it does not compromise the deliverable, and the developer did not fabricate anything (Alpaca credentials are genuinely present and every caveat is disclosed in the artifact bodies).

---

## 2. Findings

### Backend Findings

**B1 — GAP (observation, not fixed): The credentialed ≥10-window headline is `partial`/`unknown`, not "MET".**
The dev handoff status line (`docs/handoffs/goal-tradable_wall-iter-3-dev.md:6-9`), the QA summary ("Credentialed requirement: Met"), and the implementation summary ("clears the target", `reports/phase-goal-tradable_wall-iter-3-implementation-summary.md:65`) all frame the credentialed acceptance headline as achieved. Applying judgment-rubric §2 ("truly complete") and §5 (quality floor), that framing overstates the durable evidence:
- The only credentialed proof path, `tests/test_event_recording_integration.py:43-134`, **never returned a pytest PASS** — the dev handoff (`:196-205`) states the process was killed mid-verification, "no pytest PASS/FAIL was captured."
- The DoD's second credentialed clause — "the pinned event's drill-in shows the five-state timeline at the 300-test" — was **not demonstrated**: the handoff (`:128-130`) admits the AAPL replay "did not finish inside a bounded verification window"; only a JPM 295-entry timeline was shown as a proxy.
- The 15 datasets are **ephemeral**: `tests/test_event_recording_integration.py:54` records into `tmp_path/"datasets"`, and I confirmed the persistent store `apps/backend/.data/datasets/` holds only 7 pre-existing Jul-3 datasets — none from this run. Per rubric §5, "Data/metric is X" needs a re-openable computing artifact; a since-GC'd temp dir is not one.

This is a GAP, **not** fabrication or an IMPORTANT defect: I independently verified the Alpaca credentials are genuinely present and valid in this environment (`AlpacaAdapter().is_available()` == `True`, `ALPACA_API_KEY` length 26 — booleans only, values never read), so the recording narrative is real, not invented; and every caveat above is disclosed in the artifact bodies. Crucially, the phase spec (`docs/phases/goal-tradable_wall-iter-3.md:86`) makes this headline operator-gated and states it "keeps J-03 short of full `passing`" — so it does not block the phase's real deliverable. Per rubric §7, the honest status a fresh-context skeptic would record for the credentialed headline is `partial`/`unknown` (recording path exercised for real but not persisted; pinned-AAPL drill-in + integration PASS both `unknown`). Documented, not fixed: editing the handoff's characterization is not an auditor code-fix, and the gap is exactly the operator-gated one the spec designed for. *(Noting the rubric-vs-handoff disagreement per the rubric's instruction.)*

**B2 — OBSERVATION: detail route adds a per-request `DatasetStore.list()` scan.**
`enrich_with_tape_timeline` → `_matching_dataset` (`app/research/setups.py:339`) calls `dataset_store.list()` (directory scan + per-file checksum) on every `GET /research/setups/{id}` request. Confined to the detail route — `list_setups`/`compute_setups` are untouched and provably free of any dataset reference (guarded by `test_compute_setups_itself_never_touches_the_dataset_store`). Cheap at today's dataset counts, scales linearly. Flagged honestly by the dev; a J-04 hot-path item, not a defect.

### Frontend Findings

None — `Frontend Present: no`. No UI files in the diff; the drill-in rendering is J-05's scope, correctly out of scope here.

### Test Findings

**T1 — GAP (not fixed): the real-credential-value scan is narrower than the DoD wording.**
`tests/test_no_credential_in_artifacts.py:130-145` (`test_real_credential_values_if_configured...`) scans only J-03's own code files + fixture (`_code_files() + _fixture_files()`), whereas the DoD (`docs/phases/goal-tradable_wall-iter-3.md:83`) says "no credential literal appears in **any** source file, fixture, log, test artifact, or **report**." Mitigated to negligible risk: my own repo-wide grep for the actual 26-char key and 44-char secret values returned **0 files across the entire tree** (tracked + untracked, including all `reports/` and `docs/handoffs/`), so the real-world state is clean everywhere the DoD names — the test's scope is narrower than its docstring implies, but no leak exists. Documented, not fixed (GAP-level; widening the scan is scope creep).

**T2 — OBSERVATION: the committed keyless fixture exhibits only one of the four meaningful states.**
The join headline test (`tests/test_setups.py::test_join_path_matches_the_committed_fixture_and_returns_the_exact_five_state_timeline`) asserts an exact 4-entry timeline that is entirely `seller_control` — because the committed fixture is a thin ~1-minute real PG slice. The assertion is genuinely tight (exact timestamps + states + confidences via `pytest.approx`), and the join code is state-agnostic (the dev's JPM reconstruction produced `buyer_control` transitions), so this is a fixture-coverage note, not a defect.

**T3 — OBSERVATION (carried from reviewer): no explicit "malformed config rejected at load" test.**
The spec's error case "malformed padding/selection config → rejected at load" has no test. `Config` has no `__post_init__` validation anywhere codebase-wide, and the four `recording_*` fields are Python literals with no external/operator input path, so the risk is negligible. Consistent with the ~150 existing config fields; adding validation for only these four would be an inconsistent one-off.

---

## 3. Domain Assessment

The core join logic is correct and disciplined. `enrich_with_tape_timeline` (`app/research/setups.py:376-385`) returns a NEW dict (never mutates the event), replaces only `tape_timeline`, and serves every other field verbatim — single source of truth preserved (`compute_setups` alone owns band/reaction/forward-return values). `_matching_dataset` (`:324-347`) joins by `symbol` equality + numeric-epoch window containment (via the shared `parse_utc_epoch`, deliberately avoiding a lexicographic string-comparison inversion at fractional-second precision), with a deterministic `(created_utc, id)` tie-break. `_tape_timeline` (`:350-373`) replays through the frozen engine and collapses to state transitions using the `HistoryBuffer.note_state` idiom, reusing `Config.history_marker_states` (rather than a second hardcoded "which states matter" concept) and reconstructing real UTC instants as `epoch_anchor + logical_ts` (the same reconstruction `serialize_history` uses). The static guards (`test_setups_join_reuses_dataset_store_replay_never_a_second_tape_engine`, `test_compute_setups_itself_never_touches_the_dataset_store`) mechanically enforce the "never a second engine, never in the shared scan loop" architecture.

No lookahead violation: the timeline is post-hoc descriptive evidence of what the tape did around the touch (the reaction after the touch is the point), while the as-of-sensitive values (morning map, reaction, forward returns) are computed by the frozen `compute_setups` and served untouched.

Anti-goal rails all hold, verified directly:
- **No execution path** — no brokerage/order code added; the recording driver only drives the existing `POST /research/datasets`.
- **Frozen foundations byte-identical** — `app/engine/`, `datasets.py`, `levels.py`, `tradability.py`, `backtests.py`, `bars.py`, and the Alpaca adapter are all **absent from the diff** (0 changed each); the tracked diff is exactly `config.py`, `routes.py`, `setups.py`, `test_setups.py`, `test_setups_api.py`.
- **Immutable data** — reuses `record_from_source`/`DatasetStore` unchanged; the driver's split assignment (`split_for_event`) is a pure sha256 digest, deterministic, no wall-clock.
- **Feed honesty / no pooling** — the committed fixture is `data_feed=sip` verbatim; single feed per dataset.
- **Keys never committed/logged** — `.env` and `.data/` are gitignored; repo-wide grep for the real credential values = 0 hits; the recording driver counts a 422 as `BLOCKED` honestly (`record_event_windows.py:194-199`) and the integration test skips honestly rather than silently passing (`test_event_recording_integration.py:43-50`).
- **`config_fingerprint`** re-computes to `4d665603569b9dbf`; the four new `recording_*` fields are correctly in the exclusion set (perturbing them leaves the fingerprint unchanged), and the fingerprint is non-vacuous (a genuinely fingerprinted field such as `primary_window`/`min_trade_speed` does move it).

Regression posture: my own targeted run of all 65 new/touched tests passed (1 integration test skipped honestly); the review and QA reports both independently recorded the full backend suite at **1307 collected / 1300 passed / 0 failed / 0 errors / 7 skipped**, corroborated here by the frozen-file diff-absence and the re-verified fingerprint. Not re-verified by me in this pass: the full ~6-minute suite end-to-end (the reviewer reran it independently; I relied on that plus my 65-test subset and the structural checks above).

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found. Every finding is GAP- or OBSERVATION-level; fixing any of them (widening the credential scan, adding config validation, expanding the fixture, re-characterizing the handoff) would be scope creep, which the auditor protocol forbids.

---

## 5. Recommended Next Step

Proceed to **J-04 (edge report / `structure_tape_map`)**, extending the existing era-3 `edge_report.py` additively (never a second edge computation), with two explicit carries:

1. **The J-04 planner must NOT assume the 15 credentialed datasets persist.** They were recorded into an ephemeral pytest temp dir and are gone; the persistent `apps/backend/.data/datasets/` store holds only the 7 pre-existing datasets. To durably populate real event-window datasets before J-04 backtests over them, an operator must run `apps/backend/scripts/record_event_windows.py` directly (it writes to the real `.data/datasets` store). The credentialed integration test (`TAPEOLOGY_LIVE_INTEGRATION=1 pytest tests/test_event_recording_integration.py`) is safe to re-run for a clean native PASS but, by design, records into a temp dir — it is a test, not a persistence run.

2. **The evaluator should record J-03 as `partial`, not full `passing`** — keyless substrate passing (join + fixture + tests + no regressions), credentialed headline operator-gated and currently `unknown` (recording ran ephemerally; pinned-AAPL drill-in and integration PASS not captured). This matches the spec's own stated expectation that this iteration "land `partial`, not full `passing`."

Watch-items carried forward unchanged: (a) the ~4m43s full-panel scan (audit B2) is J-04/J-05's hot path — plan a persisted/cached scan; (b) the audit-B1 boundary-label contract fix remains J-05's scope, and was neither resolved nor regressed here.
