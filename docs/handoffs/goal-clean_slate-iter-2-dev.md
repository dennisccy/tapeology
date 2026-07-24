# goal-clean_slate-iter-2 Dev Handoff

**Phase:** goal-clean_slate-iter-2 (J-02: "Frontend + WS demolition — the two-page product")
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete

## What Was Built

Nothing new — this is a demolition iteration. J-02 severed the WS `thesis`/`hint` frame merge and
its last-surviving `ResearchRegistry` stub callers, trimmed the canonical nav route list to
Cockpit + Structure, and deleted the frontend pages/components/functions/types that served the
now-404 journal/studies/performance surfaces — while proving, live in a browser, that both charts
and every other kept cockpit/structure behavior still work exactly as shipped.

- **Backend WS merge removal (`app/main.py`)**: deleted `frame["thesis"] =
  _thesis_projection(ticker)` / `frame["hint"] = _hint_projection(ticker)` and both helper
  functions. The WS frame is now the engine projection only (`serialize_stream(engine.snapshot())`
  sent verbatim) — no additive research keys.
- **`ResearchRegistry` stub removal (`app/research/routes.py`), same commit as the WS merge
  removal**: deleted the `_monitors` dict and the `monitor_for`/`projection_for`/
  `_surviving_projection`/`hint_projection_for` methods iter-1 had kept alive as permanent
  `None`-returning stubs ONLY because the WS merge still called them. `ResearchRegistry` now owns
  exactly what its name says: the store and the two background job managers (backtests,
  edge-report compute). This closes iter-1's own carried-forward gap (dev handoff Known Issue #4 /
  audit finding B2).
- **Nav route trim (`app/meta.py`)**: `UI_ROUTES` cut from 6 rows to exactly 2 — Cockpit (`/`) and
  Structure (`/structure`). `GET /meta/ui-routes` now returns exactly
  `{"routes": [{"path": "/", "label": "Cockpit", "nav": true}, {"path": "/structure", "label":
  "Structure", "nav": true}]}` (verified byte-exact against TC-2). No frontend nav component was
  touched — `NavBar.tsx` already renders this endpoint's response verbatim with no hardcoded
  fallback list, confirmed by an empty `git diff` on that file.
- **`tests/test_meta_routes.py` updated to the 2-route contract**: two tests rewritten to assert
  the 2-row payload; two tests deleted (`test_ui_routes_includes_performance_now_its_page_ships`,
  `test_ui_routes_represents_journal_detail_honestly` — both asserted routes that no longer
  exist); two tests left byte-unchanged
  (`test_ui_routes_every_entry_carries_path_and_label`,
  `test_ui_routes_includes_structure_now_its_page_ships`).
- **Deleted 3 frontend pages**: `apps/frontend/app/journal/` (incl. `[id]/`), `app/studies/`,
  `app/performance/`.
- **Deleted 11 frontend components**: `JournalTable`, `JournalDetailView`, `JournalFilterBar`,
  `ThesisStrip`, `HintDock`, `HintLog`, `SoundCue`, `StudyList`, `StudyCreateForm`,
  `StudyResultsView`, `AnalyticsView`.
- **`lib/api.ts`**: deleted the 14 named functions (`declareThesis`, `resolveThesis`,
  `recordAction`, `saveReview`, `fetchActiveThesis`, `fetchActiveHint`, `fetchHints`,
  `fetchJournal`, `fetchJournalDetail`, `fetchAnalytics`, `createStudy`, `fetchStudies`,
  `fetchStudy`, `cancelStudy`) plus their now-orphaned type imports; also fixed 4 comments on
  KEPT functions (`fetchBacktest`, `fetchSetups`, `triggerEdgeReportCompute`,
  `cancelEdgeReportCompute`) that cited the deleted functions as design-precedent — a plain
  substring grep (TC-11's own methodology) would otherwise still have matched this file even
  after every function body was gone. `fetchTaxonomy` is untouched — `FeedBasisBadge.tsx`'s only
  caller.
- **`lib/types.ts`**: deleted the thesis/hint/journal/study/analytics type families
  (`ThesisVerdict`, `ThesisStatement`, `ActionMark`, `ThesisMarks`, `ThesisGeometry`, `RiskFlag`,
  `ManagementStance`, `DistanceToInvalidation`, the checklist family, `ThesisProjection`,
  `TaxonomySetup`, `SoundCueTaxonomy`, `HintsTaxonomy`, `StudiesTaxonomy`, the study result types,
  `AnalyticsTaxonomy`, `ExcursionTaxonomy`, `MistakeTag`, `ThesisGrades`, the excursion types,
  `JournalRow`, `JournalTimelineRow`, `ExecutionCheck`, `JournalDetailThesis`,
  `StatementFinalStatus`, `SavedReview`, `JournalDetail`, the segregated-analytics family,
  `JournalFilters`, `DeclareResult`, `Hint`); slimmed `ResearchTaxonomy` from a ~90-line,
  dozen-optional-field interface down to its actual served shape, `{ feed_basis:
  FeedBasisTaxonomy }` — verified against the real captured payload
  (`runs/goal-session-clean_slate/iter-1/kept-route-after.txt.taxonomy-body.json`, exactly
  `{"feed_basis": {...}}`, no other key); dropped `thesis?`/`hint?` from `TapeSnapshot`. `Analytics`
  and 3 sibling names also survive as PROSE inside 3 comments on KEPT interfaces
  (`RecordBarSeriesResult`, `BacktestResult`, `Backtest`) that cited the deleted types as
  precedent — fixed for the same TC-11-substring reason as the `api.ts` comments above.
  `TaxonomyEnum` stays — `FeedBasisTaxonomy.feeds` (a KEPT type) uses it.
- **`lib/useTapeStream.ts`**: verified via inspection AND an empirical `tsc --noEmit` clean pass —
  it parses the WS payload structurally (`JSON.parse(event.data) as TapeSnapshot`) with no named
  reference to `thesis`/`hint` anywhere in the file. No edit was needed, as the plan's own note
  predicted.
- **`app/page.tsx`**: removed the thesis/hint integration in full — the `fetchActiveThesis`
  import, the `Hint`/`ThesisProjection`/`ThesisStrip`/`ThesisPrefill` imports, the
  `survivingThesis` state and its post-Stop `GET /research/thesis/active` read inside
  `handleStop`, `hintPrefill`/`handleHintDeclare`, the live `<ThesisStrip>` render (collapsed the
  now-single-child `<>...</>` fragment down to `<Cockpit snapshot={snapshot} />` directly), the
  post-stop "surviving thesis" ternary branch (collapsed into the plain `failure`/idle chain), the
  `thesis` prop passed to `<PriceChart>`, and the `onHintDeclare` prop passed to `<Cockpit>`.
- **`components/Cockpit.tsx`**: dropped the `HintDock` import/render, the `onHintDeclare` prop
  from the component's own signature, and the `Hint` type import — not just the render call, per
  the plan's explicit warning that this is a real orphaned-prop target. Simplified the now-single-
  child `<div className="flex flex-col gap-4">` wrapper around `TapeStatePanel` away (HintDock was
  its only sibling) — visually identical (HintDock rendered nothing in the common no-hint case
  already; this only removes a now-pointless wrapper div). `QuotePanel`/`RecentTradesPanel`/
  `FeaturesPanel`/`TapeStatePanel`/`ObservationsPanel`/`EventLogPanel` are byte-untouched.
- **`components/PriceChart.tsx`** (T-8 veto-class file — see Known Issues #1 for a self-caught
  correction made mid-iteration): removed the `thesis`/`ThesisProjection` prop, the `VERDICT_COLORS`/
  `PRICE_LINE_COLORS`/`MARK_COLOR` color dicts (used ONLY by the removed geometry construction),
  and the thesis-derived half of the `extraMarkers` useMemo (the `thesisSpecs` computation) — tape-
  state markers (`stateSpecs`) are now the useMemo's only output. The `extraMarkers`/
  `extraPriceLines` PROP-PASSING SEAM into `StructureChart` is preserved exactly as the phase
  spec's own wording requires ("tape-state markers keep flowing through the SAME
  extraMarkers/extraPriceLines seam") — `extraPriceLines` is now a stable, referentially-constant
  empty array (`NO_PRICE_LINES`, module-scope) rather than a per-render fresh `[]`, so
  `StructureChart`'s own `[extraPriceLines, chartReady]` effect never re-fires needlessly.
  `StructureChart.tsx` itself is untouched (`git diff` empty, verified repeatedly through the
  iteration).

## Files Changed

Backend + frontend, `git diff --stat`: **10 files changed, 99 insertions(+), 1506 deletions(-)**,
plus 14 files deleted (3 pages + 11 components).

- `apps/backend/app/main.py` — deleted WS `thesis`/`hint` frame merge + both projection helpers
- `apps/backend/app/research/routes.py` — deleted 4 dead `ResearchRegistry` stubs + `_monitors`;
  rewrote the class docstring
- `apps/backend/app/meta.py` — trimmed `UI_ROUTES` to 2 rows
- `apps/backend/tests/test_meta_routes.py` — updated 2 tests to the 2-route contract, deleted 2,
  left 2 unchanged
- `apps/backend/tests/test_profile_equivalence.py` — deleted ONE test (see Known Issues #2); every
  other test in the file (profile registry / config-fingerprint / backtest-overlay coverage) is
  untouched
- **Deleted:** `apps/frontend/app/journal/page.tsx`, `apps/frontend/app/journal/[id]/page.tsx`,
  `apps/frontend/app/studies/page.tsx`, `apps/frontend/app/performance/page.tsx`,
  `apps/frontend/components/{JournalTable,JournalDetailView,JournalFilterBar,ThesisStrip,HintDock,
  HintLog,SoundCue,StudyList,StudyCreateForm,StudyResultsView,AnalyticsView}.tsx`
- `apps/frontend/lib/api.ts` — deleted 14 functions + their now-dead type imports; fixed 4 stale
  precedent-citation comments
- `apps/frontend/lib/types.ts` — deleted ~30 thesis/hint/journal/study/analytics
  interfaces/types; slimmed `ResearchTaxonomy`; dropped 2 fields from `TapeSnapshot`; fixed 3
  stale precedent-citation comments
- `apps/frontend/app/page.tsx` — removed the full thesis/hint integration (imports, state,
  handlers, JSX, props)
- `apps/frontend/components/Cockpit.tsx` — dropped `HintDock` + `onHintDeclare` + `Hint` import;
  simplified the now-single-child wrapper div
- `apps/frontend/components/PriceChart.tsx` — removed the thesis-geometry overlay construction
  only; the `extraMarkers`/`extraPriceLines` seam into `StructureChart` stays wired
- `runs/goal-session-clean_slate/iter-2/kept-route-after.txt` (+ 8 browser-evidence screenshots +
  1 captured WS-frame JSON) — the I-9 byte-comparison re-capture and TC-3–TC-9 evidence

**`apps/frontend/components/StructureChart.tsx` diff: empty** (`git diff` returns nothing),
verified repeatedly through the iteration, including after the mid-iteration `PriceChart.tsx`
correction in Known Issues #1.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1162 passed, 1 failed, 0 errors, 7 skipped** (1170 collected; iter-1's post-J-01 baseline
was 1165 passed / 1 failed / 7 skipped / 1173 collected — a reduction of exactly 3 tests: the 2
sanctioned `test_meta_routes.py` deletions plus the 1 `test_profile_equivalence.py` T-14
correction in Known Issues #2. No test file was added or removed as a FILE this iteration — both
edited files still exist; only specific test FUNCTIONS inside them were deleted, per the plan's
own explicit instruction for `test_meta_routes.py` and per the T-14 correction below for
`test_profile_equivalence.py`).

The **1 failure** is the SAME single pre-authorized failure as iter-1:
`test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest` (proxying the `journal`
MCP tool to now-404 `GET /research/journal`). `test_mcp_server.py` is untouched this iteration —
its 15-tool contract update is explicitly J-03's job (this iteration's Out-of-Scope list, honored:
`git diff` on that file is empty).

Also verified directly (not just via pytest):
- `python -c "import app.main"` succeeds with no `NameError`/`AttributeError`/`ImportError`
  (TC-1).
- `GET /meta/ui-routes` returns exactly the TC-2 payload (curled against the running dev backend).
- `apps/frontend`: `npx tsc --noEmit` completes with **zero errors** (TC-10) — run twice, once
  before and once after the Known Issues #1 correction, both clean.
- The chart guard suites (`test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`,
  `test_price_chart_confluence.py`) — 33 tests, all pass, all three files' `git diff` empty
  (TC-18).
- `test_copy_discipline.py` — unedited (`git diff` empty), re-run, 0 failed (TC-13; its frontend-
  literal walk is a dynamic glob, so it needed no manual change and simply scans fewer files now).
- Config/pin discipline: `config_fingerprint()` still prints `4d665603569b9dbf`;
  `apps/backend/app/config.py`'s `git diff` is empty; all 13 fingerprint-pin assertion occurrences
  (grep count) are unchanged (TC-15).
- `apps/backend/app/mcp/__init__.py`'s `git diff` is empty (untouched, as required).
- `apps/frontend/components/NavBar.tsx` and `TopBar.tsx` — both `git diff` empty (neither needed
  editing, confirmed).
- T-12-style grep for all 25 doomed identifiers (the 14 `api.ts` functions + 11 component names +
  `onHintDeclare`/`handleHintDeclare`/`hintPrefill`/`survivingThesis`/`ThesisPrefill`) across
  `apps/frontend/`, excluding `docs/goal-archive`/`runs/goal-session*`: **zero hits** (TC-11);
  `fetchTaxonomy` still hits in both `lib/api.ts` and `FeedBasisBadge.tsx`.
- TC-16 (never touch a historical record): `git status --porcelain` on `docs/goal-archive/`,
  `runs/goal-session-clean_slate/` (excluding the new iter-2 evidence files this iteration
  itself is required to write), and `reports/` shows only the pipeline's own
  `telemetry.jsonl`/`trace.jsonl` housekeeping — no historical row touched.

### I-9 byte-comparison re-capture (TC-14)

Re-captured all 28 kept routes against the running dev backend (`runs/goal-session-clean_slate/
iter-2/kept-route-after.txt`, same 28 routes as iter-1's capture). Result: **25 of 28 identical**,
1 sanctioned diff, 2 diffs that are a verified non-issue (both documented at length inline in the
capture file's own header comment):

1. `meta.ui-routes` — **sanctioned**, this iteration's own documented change (6 rows -> 2 rows).
2. `research.backtests.list` / `research.pnl_ledger` — **not a regression**. Root cause: the
   journal DB path is config-default-relative (`journal_db_path_resolved()`), resolved against
   the backend process's own cwd. My dev session (`bash scripts/dev.sh`, which `cd`s into
   `apps/backend/` before `uvicorn`) reads `apps/backend/tapeology_journal.db` — this project's
   real, full-history dev store (203 backtests / 1 pnl row, oldest dated 2026-07-03, entirely
   predating this session). Iter-1's capture instead read a near-empty `tapeology_journal.db` that
   lives at the repo root (0 rows) — a leftover of whatever cwd the goal-mode pipeline's own
   backend launch used for that capture. **Proof this is a launch-cwd artifact, not a code
   regression**: pointing this iteration's own code (`JournalStore` + `TestClient`, no HTTP
   restart) at that SAME repo-root DB file reproduces iter-1's exact captured hashes byte-for-byte
   (verified inline in this handoff's investigation and recorded in the capture file's header).
   No route handler, store method, or serialization this iteration touches is anywhere near the
   backtests/pnl_ledger read path — `app/research/backtests.py`, `app/research/pnl_ledger.py`,
   `app/research/store.py`, and `app/config.py` all have empty `git diff`.

## Known Issues

**This section documents T-14 inventory corrections** — goal.md's own protocol for when in-era
reality contradicts its (very thorough) inventory: surface it, fix it minimally and honestly, never
improvise a bigger change. Two such corrections this iteration, both caught by re-running the
guard-test suite after each set of edits rather than trusting the plan's prose alone:

1. **`PriceChart.tsx`'s `extraPriceLines` prop-passing seam had to be RESTORED after my first
   pass over-deleted it.** My first edit removed the entire `extraPriceLines` useMemo (reasoning:
   it was 100% thesis-geometry-derived, so with `thesis` gone it would only ever evaluate to `[]`)
   and dropped the `extraPriceLines={extraPriceLines}` prop from the `<StructureChart>` call
   entirely, relying on `StructureChart`'s own `extraPriceLines = []` default parameter. This
   compiled clean (`tsc --noEmit` passed) but FAILED
   `test_cockpit_chart_upgrade.py::test_price_chart_passes_live_and_overlay_props_to_the_renderer`
   — a source-introspection guard that pins the literal substring `extraPriceLines=
   {extraPriceLines}` in `PriceChart.tsx`'s source, independent of whether the value is ever
   non-empty. Re-reading the phase spec's own wording after the failure: "tape-state markers keep
   flowing through the SAME extraMarkers/extraPriceLines seam into StructureChart" — the SEAM
   (the prop-passing plumbing itself), not just the marker data, was meant to stay wired. Fix:
   restored a module-scope, referentially-stable `NO_PRICE_LINES: ChartPriceLineSpec[] = []`
   constant, bound it to a local `extraPriceLines`, and passed `extraPriceLines={extraPriceLines}`
   back to `<StructureChart>` — same zero-price-lines runtime behavior, but the guard's pinned
   substring (and the `ChartPriceLineSpec` type import it depends on) is back. Re-ran all three
   chart guard suites (33 tests) + `tsc --noEmit` + a fresh browser check of the AAPL band overlay
   after this fix — all clean. `StructureChart.tsx` was never touched in either pass.
2. **`tests/test_profile_equivalence.py::test_performance_page_offers_no_profile_selection_control`
   read the (now-deleted) `/performance` page's source file directly off disk and asserted no
   `<select>`/no hardcoded candidate id in it — an I-8-uncatalogued test (the file is not in
   goal.md's I-8 DELETE list, its UPDATE list, or its explicit KEEP-unmodified list) whose entire
   subject was a UI constraint on a page this very journey deletes. Once `app/performance/page.tsx`
   was gone, `Path.read_text()` raised, failing the test — a SECOND, unauthorized failure beyond
   the one pre-authorized MCP failure, which the DoD/TC-17 forbid. Fix: deleted this ONE test
   function (the file's other ~14 tests — profile registry shape, `config_fingerprint` folding,
   train/holdout backtest-overlay equivalence, the source-scan guard for `resolved_for_profile`
   callers — are pure backend coverage, untouched, still pass) and updated one docstring line in
   the module's own "Locked disciplines" list that referenced the now-nonexistent `/performance`
   panel. The file's `4d665603569b9dbf` fingerprint-pin assertion (I-9 site #6,
   `test_profile_equivalence.py:114` at `fa76460`) shifted a few lines from my docstring edit but
   is byte-identical in content and untouched in value — confirmed by grep.

Beyond those two, the T-12-style grep for a second, undocumented consumer of every deleted
symbol/component/route came back clean on every check I ran — no further gaps surfaced.

**Nothing else known to be incomplete.** J-03 (MCP contract), J-04 (fingerprint epoch bump), and
J-05's remaining sentinel clauses (Case Studies, full-suite-under-new-pin, cumulative diff-vs-
inventory) are unstarted, as scoped. `apps/backend/app/config.py`, all 13 fingerprint pins,
`apps/backend/app/mcp/__init__.py`, and `apps/backend/tests/test_mcp_server.py` are all
byte-untouched (verified by `git diff`, not just by intent). `SHOW_CASE_STUDIES = false`
(`apps/frontend/app/structure/page.tsx:335`) is still unresolved — re-verified still `false`,
still out of scope for J-02, carried forward again for whoever plans J-05. One more minor,
deliberately-NOT-fixed item: `apps/backend/app/structure/page.tsx` — wait, `apps/frontend/app/
structure/page.tsx:1305` — contains a code COMMENT with the bare word "Study" ("unlike a Study's
cancelled-but-partial results") describing why backtests differ from the now-deleted replay-study
runner. This does not trip TC-11's grep (which matches compound identifiers like
`StudyResultsView`, never the bare word "Study"), is not in this iteration's Files-to-Modify list,
and `/structure` is a high-stakes KEPT page this journey has no mandate to touch — left as-is
rather than risk an undirected edit to an otherwise-untouched file for one stale comment word.
