# goal-fast_wall-iter-4 Audit Report

**Date:** 2026-07-17
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-04 ("the operator-run compute") is genuinely built and correct. The single-flight/cancel/force/
progress/failed-state lifecycle, the five additive keyword-only hooks, the three REST subpaths, the
`peek` `compute`-field rewire, and the CLI warmer are all verified directly against source — not
trusted from the handoff — and the frozen-foundation anti-goals ("no compute on GET", "no MCP write
surface", "no divergent accelerator output", byte-identical cache methods) are mechanically guarded
and hold. The single limitation is the browser click-through (TC-15/TC-16): Chrome MCP cannot start
in this environment, which I reproduced first-hand. That gap is environmental (not a code defect),
honestly disclosed at every pipeline stage, and never faked — an acceptable, documented gap, not a
FAIL, because the capability demonstrably works at the HTTP/unit/CLI level and no code change could
close it.

---

## 2. Findings

### Backend Findings

**B1 — GAP (no fix — verified correct): "publish only after normal return" holds by construction.**
The TC-3/TC-13 promise ("a cancelled or failed run publishes NOTHING to the edge-report cache") rests
entirely on the two untouched cache methods. I read them directly: `edge_report_cache.py:297-299`
(`get_or_compute`) and `edge_report_cache.py:347-349` (`compute_and_publish`) both bind
`result = compute_fn()` FIRST and only then call `self._insert(...)` / rebind `self._hot`. A
`compute_fn` that raises `EdgeReportComputeCancelled` (from a fired `should_abort`) or any other
exception never reaches the publish lines. `git diff` confirms `edge_report_cache.py` is byte-unchanged.
This is genuinely correct, not just asserted.

**B2 — OBSERVATION: benign check-then-call TOCTOU in the cancel route.**
`routes.py:cancel_edge_report_compute` reads `snapshot()`, checks `state != "running"` → 409, else
calls `cancel()`. If the job completes between the check and the `cancel()` call, the route still
returns `{"cancelling": true}` while the job stays `done`. This is the exact `cancel_backtest`
check-then-call precedent the spec named, and the stale `cancel_event.set()` is a harmless no-op
(each `trigger()` creates a fresh event captured in the worker closure, so no cancel leaks into a
later job — verified in `edge_report_compute.py:138-140,166-169`). Not a defect; standard cooperative-
cancel semantics.

**B3 — OBSERVATION (already flagged by reviewer): misnamed CLI test.**
`test_edge_report_compute.py:423` `test_cli_missing_dataset_dir_env_falls_back_to_default_seams_
without_crashing` claims to exercise a missing dataset-dir env, but `_set_cli_env` (line 313) always
sets `TAPEOLOGY_DATASET_DIR`, so it just re-runs the bare-argv default path (redundant with the
workers-flag test). The CLI's genuine missing-env behaviour is untested, but the spec's TC list never
required it (TC-11/TC-12 are the CLI requirements and are genuinely covered — I ran the CLI myself,
see §3). Rename or add a real unset-env case. Not fixed (test-naming polish = scope creep).

### Frontend Findings

**F1 — GAP: TC-15/TC-16 browser click-through unverified (environmental).**
`structure/page.tsx` gains the button + poll `useEffect` + done/failed branches. I traced the logic
end-to-end (mount seeds `computeSnapshot` from the payload's `compute` field; the poll effect stops
the instant `state !== "running"` and re-fetches the report once on `done`; `NotComputedPanel`
renders idle/running/failed correctly) and confirmed it reuses the existing 700ms backtest-poll
pattern and the `structure-load-button` classes verbatim. `tsc --noEmit` exits 0 (I ran it). What is
NOT verified is the actual rendered click-through, because Chrome MCP fails to start —
I reproduced the identical error the dev/QA documented ("Chrome did not become ready on port 9222
within 15000ms"). Per this project's own "no screenshot ⇒ unknown, never passing" discipline, J-04's
browser leg is `unknown` this iteration. No code fix is possible (the block is environmental); the
gap must be closed by a browser-qa retry in a healthy session.

**F2 — OBSERVATION: a `cancelled` job renders the idle button.**
On `state === "cancelled"`, `NotComputedPanel` shows the default "Compute edge report" button (no
distinct cancelled copy). Acceptable — no cancel affordance is wired this iteration (the spec's UI
Evolution names only the trigger button), so a cancelled job reverting to re-triggerable idle is
reasonable. `cancelEdgeReportCompute()` exists in `lib/api.ts` but is intentionally unwired.

### Test Findings

**T1 — GAP: TC-17/TC-18 browser regression checks unverified (same environmental cause as F1).**
J-01's frozen not-computed render and J-07's `/structure` sentinel were re-verified only at the code/
SSR level (zero diff on their owned files, backend suite green). Their browser-visual regression legs
share the Chrome MCP block. The frozen headline/detail/register strings are byte-unchanged in the
diff (the button/progress/error nodes are strictly appended below them — `page.tsx:319-348`), so a
visual regression is very unlikely, but it is not screenshot-confirmed.

**T2 — (verified strength, not a defect): the equivalence proofs are non-vacuous.**
TC-14a (`test_edge_report.py:1104`) asserts byte-identity on a genuine 3-cell report AND that the
progress hook actually fired (`assert progress_events`). TC-14b (`:1133`) raises
`EdgeReportComputeCancelled`, asserts `cache.lookup(...) is None` (nothing published) and exactly one
backtest persisted (abort fired between pairs, first pair completed). This satisfies iter-3's lesson
("the equivalence test passes" is not sufficient — demand a mutation/behavior probe) exactly.

---

## 3. Domain Assessment

The core domain logic is sound and the module boundaries are respected. `EdgeReportComputeManager`
is deliberately single-flight (one `self._snapshot` slot, not a per-id dict), which is the right shape
for "the one edge-report compute". The concurrency handling is correct on inspection: every snapshot
mutation is a fresh-dict rebind under `self._lock`; readers take a local reference and receive a
2-level-deep copy (`_copy_snapshot`); `_publish_progress`/`_resolve` both guard on `id` so a
superseded worker cannot poison a newer job; and the worker closure captures THIS job's
`cancel_event` (never the rebindable `self._cancel_event`), so cancels never leak across jobs.
Single-flight holds because a new job starts only when the current one is terminal, and terminal state
is set by `_resolve` at the very end of the worker — no two sweeps ever run concurrently.

The compute path itself is untouched research logic with additive-only seams: `progress`/
`should_abort` thread into `_split_cells`'s existing loop guarded by `is not None` checks (byte-
identical when omitted); `_count_eligible_pairs` reuses `_dataset_event` purely to pre-size the
progress counter and is not even called when `progress is None`; `force` selects
`compute_and_publish` vs `get_or_compute`, both already shipped. No lookahead, no new randomness, no
wall-clock in the research artifact (the snapshot's `started_utc`/`finished_utc` are job bookkeeping,
explicitly "never a research value", and are absent from the report shape TC-7 pins byte-identical).

I independently ran the CLI warmer end-to-end against the committed `datasets_j03` fixture in a scoped
temp env: the cold run exits 0, prints the "0 backtest(s) to run" / completion summary, and writes a
report carrying the correct register string ("simulated — assumed fees/slippage — not indicative of
live results" — no prediction/advice language); the warm re-run exits 0 in 0.08s (TC-12's <5s ceiling).
The PG fixture honestly resolves zero eligible pairs → the deterministic all-empty report, exactly as
the handoff and QA describe.

Verification tally (independently reproduced): 121 targeted tests exit 0
(`test_edge_report_compute` + `test_edge_report_api` + `test_edge_report` + `test_mcp_server`);
`test_edge_report.py` collects 50, `test_edge_report_compute.py` collects 20; `config_fingerprint()`
= `4d665603569b9dbf`; `TOOL_NAMES` == 18; `git diff HEAD` shows zero diff on `edge_report_cache.py`,
`mcp/__init__.py`, `config.py`, `levels.py`, `tradability.py`, `backtests.py`, `bars.py`,
`datasets.py`, `dataset_index.py`; `tsc --noEmit` exits 0.

**Definition of Done:** 15 of 16 items fully met and independently confirmed. The single unmet item is
DoD #1 (browser-qa pass of J-04 via TC-15) plus the browser regression legs (TC-17/TC-18) — all
blocked by the same environmental Chrome MCP failure, honestly marked `unknown`.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found. The implementation is correct and byte-scoped exactly
to the spec; the only gap is environmental browser verification, which no code change can close (the
Chrome MCP bridge will not start in this session — reproduced first-hand). The two OBSERVATION-level
items (B3 misnamed test, F2 cancelled-state copy) are polish, not defects — fixing them would be scope
creep. GAP-level items (F1/T1) are documented for the browser-qa retry, not fixed.

---

## 5. Recommended Next Step

Accept this iteration's HTTP/unit/CLI evidence as sufficient for the compute capability itself, and
**carry the browser click-through (TC-15/TC-16) and browser regression (TC-17/TC-18) forward as an
explicit open item** — to be completed by browser-qa-agent in a session where Chrome MCP starts
(the diagnostic trail is in the dev handoff; a fresh session or manual Chrome/DevTools bring-up on the
scoped port 8391/3391 fixture stack is the recovery path). The code is ready; only the visual proof is
outstanding. Once that screenshot exists, J-04 is unambiguously `passing`. Then proceed to **J-05**
("resumable + parallel sweep") per goal.md's dependency order, which gives the accepted-but-inert
`sub_cache=`/`workers=` hooks their real effect.
