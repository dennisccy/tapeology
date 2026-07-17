# Iteration 4 — Coherence Audit

**Iteration:** goal-fast_wall-iter-4
**Date:** 2026-07-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Iteration J-04 builds `EdgeReportComputeManager` (new file `apps/backend/app/research/edge_report_compute.py`)
and rewires `peek_strategy_comparison_report`'s `compute` field. The blueprint's Data Contract already
pre-registered a "Compute-job snapshot" row at baseline (owner `edge_report_compute.py` /
`EdgeReportComputeManager`, endpoint `GET /research/edge-report/compute`); this iteration only widened
that row's field list to match what got built (confirmed via `git diff <snapshot-sha> -- runs/goal-session-fast_wall/state/blueprint.md`
— the `-` side already shows the row pointing at the same single owner/endpoint before this iteration's
edit). No new row was added, no nav-skeleton line changed.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Compute-job snapshot (`id`, `state`, `force`, `started_utc`, `finished_utc`, `error`, `progress{phase,backtests_total,backtests_done,backtests_from_cache,current}`) | OK | Single writer: `EdgeReportComputeManager.trigger`/`_resolve`/`_publish_progress` (`apps/backend/app/research/edge_report_compute.py:116-193`). Single reader path: `GET /research/edge-report/compute` → `registry.edge_report_compute.snapshot()` (`apps/backend/app/research/routes.py:381-387`) AND the embedded `compute` field on `GET /research/edge-report` → the SAME `registry.edge_report_compute.snapshot()` call (`routes.py:342-346`). Shape matches the blueprint row field-for-field. |
| Not-computed edge-report payload (`status`, `detail`, `dataset_count`, `register`, `compute`) | OK | Still the sole `peek_strategy_comparison_report` (`edge_report.py:606-644`); this iteration only threads a `compute=` passthrough kwarg into the existing dict literal (`edge_report.py:643-644` sets `"compute": compute` verbatim, never re-derived) — confirmed by `test_peek_compute_field_embeds_whatever_is_passed_verbatim` (`tests/test_edge_report.py`). |
| 3-way edge-report cells (`train`/`holdout`/`surviving_train_cells`) | OK | Still the sole `_compute_strategy_comparison_report` (`edge_report.py:225-...`); the new `progress=`/`should_abort=` kwargs are optional cooperative hooks into the SAME untouched `_split_cells` loop (pooling/ordering/aggregation code byte-for-byte unchanged per the function's own docstring and TC-14a's `json.dumps` byte-identity assertion at `tests/test_edge_report.py:449`) — not a second computation path. |
| Route surface for `/research/edge-report*` | OK | The three new routes (`trigger_edge_report_compute`, `get_edge_report_compute`, `cancel_edge_report_compute`, `routes.py:362-401`) are subpaths of the existing section, resolved through the SAME four existing dependency seams (`get_registry`/`get_dataset_store`/`get_bar_store`/`get_edge_report_cache`) — no second store/cache construction path. Confirmed zero diff on `edge_report_cache.py`, `levels.py`, `tradability.py`, `backtests.py`, `bars.py`, `datasets.py`, `dataset_index.py`, `app/mcp/__init__.py` via `git diff <snapshot-sha> -- <those files>` (empty output). |

No duplicate computation and no non-canonical source found. No new displayed value is missing from
the Data Contract — the compute-job snapshot's expanded field list is a refinement of an
already-registered row, not a new unregistered concept. The frontend never recomputes any of this:
`structure/page.tsx`'s `NotComputedPanel` progress line does simple string interpolation of
`compute.progress.backtests_done` / `backtests_total` (a re-format, not a computation), and the poll
effect's two fetches (`fetchEdgeReportCompute()` → `GET /research/edge-report/compute`,
`fetchEdgeReport()` → `GET /research/edge-report`) both hit the canonical endpoints.

## Information Architecture check

No new page or route was added. The button/progress-line/error-line all live inside the EXISTING
`/structure` page's EXISTING `NotComputedPanel` (`apps/frontend/app/structure/page.tsx:1011-1063`),
which is the blueprint's own pre-registered canonical home for J-04
(`/structure` → **Edge Report** section — blueprint.md's Feature/journey homes table). No parallel
shell, no second "compute" entry point anywhere else in the diff.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| "Compute edge report" button + progress line (`/structure`, Edge Report section) | OK | `apps/frontend/components/NavBar.tsx` — renders nav links dynamically from `GET /meta/ui-routes`; confirmed untouched this iteration (`git diff <snapshot-sha> -- apps/frontend/components/NavBar.tsx` empty) and confirmed `apps/backend/app/meta.py:30` still registers `{"path": "/structure", "label": "Structure", "nav": True}` (also untouched). `/structure` is therefore still 1 click from the persistent top nav; the new button is on that same page (0 extra clicks), well within the ≤2-click bar. |
| `POST /research/edge-report/compute/cancel` | OK (no UI caller yet — not a violation) | Implemented and tested at the REST layer, exported as `cancelEdgeReportCompute()` in `lib/api.ts`, but not wired to any button this iteration — the iter spec's IN SCOPE list only requires a trigger button, and the UI surface map documents this explicitly as a backend-only addition. Not a hidden *feature* (there is no UI affordance implying it exists), so this is not a "no navigation path" violation. |

No duplicate-home, no parallel-shell, no undiscoverable-route findings.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Every sibling report this iteration (dev handoff, audit → `PASS_WITH_GAPS`, review → `PASS_WITH_NOTES`,
  QA → `PASS_WITH_NOTES`, ux-regression → `UX-REGRESSION-WARN`) converges on the same single gap: Chrome
  MCP failed to start in this session ("Chrome did not become ready on port 9222 within 15000ms"),
  reproduced independently by four separate agents, so TC-15/TC-16's live button click-through has no
  screenshot. This is a browser-QA/visual-verification concern, not a coherence one — the static
  evidence (source tracing, `tsc --noEmit`, curl-verified live HTTP trigger→running→done/failed cycle
  against a real scoped backend, SSR-HTML structural check) all confirms the button reads/writes through
  the canonical endpoints and lives in its registered home. Recorded here only so this gate's PASS is not
  mistaken for a claim that the button has been visually observed — it has not, and that remains open for
  browser-qa-agent in a healthy session.
- No unregistered-value or formatting-drift observations — the compute-job snapshot's TypeScript type
  (`lib/types.ts` `EdgeReportComputeSnapshot`/`EdgeReportComputeProgress`) matches the Python/blueprint
  shape field-for-field, and the new panel reuses the existing amber degraded-state container and
  `structure-load-button` classes verbatim (no new visual language introduced).
