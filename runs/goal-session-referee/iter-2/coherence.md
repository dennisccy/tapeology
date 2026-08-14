# Iteration 2 — Coherence Audit

**Iteration:** goal-referee-iter-2
**Date:** 2026-08-14
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

This iteration is backend-only (J-02: the typed evidence-observation contract). Diff-stat confirms
exactly 3 files changed, all Python: `apps/backend/app/research/referee_evidence.py`,
`apps/backend/tests/test_referee_evidence.py`, `apps/backend/tests/test_referee_guards.py`. No
frontend file, no route file (`desk_routes.py`/`routes.py`), and no `Config` field is touched
(`grep -iE '@router|@app\.(get|post|put|delete)|APIRouter|include_router'` and a `Config` grep over
the full diff both return zero hits).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Referee evidence coverage + per-family readiness (`referee_evidence()` → `GET /research/desk/referee/evidence`) | OK — byte-identical, unchanged | `apps/backend/app/research/referee_evidence.py:134` comment: "Nothing below this line is wired into `referee_evidence()`/`GET /research/desk/referee/evidence`"; new guard test `apps/backend/tests/test_referee_evidence.py` `test_module_docstring_pins_integrity_errors_as_part_of_the_response_shape` (TC-11) plus the untouched existing J-01 fixture assertions re-run unmodified |
| New typed observation contract (`playbook_observations`, `strategy_observations`, `_observation`) | OK — matches blueprint IA row exactly, not a displayed value this iteration | Blueprint row: "J-02 evidence contract, J-03 stats core (library modules, no page of their own) \| n/a — consumed by J-04–J-09 \| —"; diff adds no route decorator anywhere, confirmed by grep |
| Matched-null records, Registry, Evaluation records, Adjudications, Promotion verdict (all other Data-Contract rows) | OK — untouched | diff-stat shows none of `referee_null.py`, `referee_registry.py`, `referee_adjudicate.py`, `pnl_scan.py` exist/changed |

No duplicate computation found: the playbook adapter (`_resolve_leaf`,
`_playbook_file_projection`) only reads values already computed and stored in each signal's own
`forward` block (`desk_forward._measure_from`'s output) — it re-formats/re-labels, never
re-measures. The strategy adapter (`_strategy_observation`) reads `trade["net_r"]`,
`dataset["epoch_anchor"]`, and `entry["logical_ts"]` verbatim from the already-joined result block
`backtests.py` recorded — no second `DatasetStore` lookup, no re-join, no re-computation of a PnL
or return value already owned elsewhere. Both are read/re-shape operations, not new computations of
an existing registered value.

The new observation contract itself is not yet in the Data Contract table because it is not (yet) a
displayed/served value — this exactly matches the iteration spec's own "Data-contract additions:
None" and the blueprint's pre-existing IA row anticipating precisely this shape. Not an
"unregistered value" WARN under skill rule A5, because A5 applies to values the iteration *displays*
outside the contract; this iteration displays nothing (confirmed: no route, no UI).

## Information Architecture check

No new page/route/feature exists this iteration (frontend diff is empty; `docs/phases/goal-referee-iter-2.md`
itself states "Frontend: (none...)", "UI surface changes: None", "Product surface delta: None visible
in the UI"). No `reports/phase-goal-referee-iter-2-ui-surface-map.md` was produced, consistent with
zero frontend change. Nothing to check for nav reachability, duplicate home, or parallel shell this
iteration.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route this iteration) | N/A | n/a |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `strategy_observations`' `_et_session_date` computes a `session_date` field using ET-calendar-date
  semantics, explicitly and deliberately different from `desk_sessions._session_date` (UTC-calendar,
  a different purpose) — disclosed in the adapter's own docstring
  (`apps/backend/app/research/referee_evidence.py`, the `_et_session_date` and `strategy_observations`
  docstrings). Both are internal, non-displayed fields today, so this is not a Data Contract
  violation. Worth a naming/label check once J-05/J-06/J-07 render observation `session_date`
  alongside any UTC-calendar `session_date` already shown elsewhere on `/desk`, so the two concepts
  read as clearly distinct to an operator rather than as the same field with two different values.
