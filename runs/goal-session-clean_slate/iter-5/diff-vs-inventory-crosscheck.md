# J-05 session-wide diff-vs-inventory cross-check

**Scope:** the cumulative diff from the session baseline (`e7865b4`, "docs(goal): open ... era 5D" —
the commit immediately before iter-0 ran, goal.md's own authoring point) through this iteration's
current working tree, restricted to `apps/` (where every I-1…I-9 disposition lives). Command:
`git diff e7865b4 --name-status -- apps/`.

**Result: 91 files changed (1 added, 51 deleted, 39 modified). Every one is accounted for against
I-1…I-9 + I-8's test dispositions + J-04's landed pin/baseline updates. Zero out-of-inventory
changes found.**

## Deletions (51) — fully accounted

| Bucket | Count | Inventory row | Verified |
|---|---|---|---|
| Backend modules | 11 | I-2 DELETE | `analytics.py, excursions.py, execution_checks.py, grades.py, hints.py, journal_rows.py, marks.py, monitor.py, stance.py, studies.py, verdict.py` — exactly the 11 named modules, no more, no less. Files confirmed physically gone (not stubbed, T-2). |
| Backend test files | 25 | I-8 DELETE (goal.md's own list, prefixed "~24") | Diff's 25 deleted test files match goal.md's I-8 DELETE list NAME-FOR-NAME exactly (the list itself contains 25 names despite the "~24" prose approximation — not a discrepancy, the source text already flags it as approximate). |
| Frontend pages | 4 | I-7 ("3 pages") | `app/journal/page.tsx`, `app/journal/[id]/page.tsx`, `app/studies/page.tsx`, `app/performance/page.tsx` — matches I-7's "journal/ (page + [id]/ detail), studies/, performance/" = 4 files for "3 pages". |
| Frontend components | 11 | I-7 (eleven components) | `AnalyticsView, HintDock, HintLog, JournalDetailView, JournalFilterBar, JournalTable, SoundCue, StudyCreateForm, StudyList, StudyResultsView, ThesisStrip` — exact name-for-name match with I-7's list. |

## Addition (1)

- `apps/backend/tests/test_fingerprint_epoch_retirement.py` — new, J-04's old-literal-retirement test (already reviewed/audited PASS at iter-4).

## Modifications (39) — fully accounted

**Backend `app/` (12 files)** — each maps to one I-row: `config.py` (I-4 field deletions),
`main.py` (I-5 lifespan+WS), `mcp/__init__.py` (I-6), `meta.py` (I-7 nav rows), `backtests.py` +
`datasets.py` (I-2 RELOCATE destinations), `edge_report.py` (I-2 comment update), `pnl_baseline.py`
(I-2 RELOCATE importer + J-04 id/title bump), `routes.py` (I-1/I-2 route+import strips), `store.py`
(I-3 method deletions), `taxonomy.py` (I-2 SLIM). Plus `setups.py` — a 2-line comment fix updating a
cross-reference that named the now-relocated/demolished `studies.py` to point at `backtests.py`
instead (where I-2's RELOCATE table moved the "tape-arming occurrence" concept) — zero behavior
change, verified via direct diff read.

**Backend `tests/` (21 files)** — three explained sub-groups, no unexplained residue:
1. **8 files via I-9's fingerprint-pin sites**: `test_timeframe_history_api.py`, `test_levels.py`,
   `test_tradability.py`, `test_backtests.py`, `test_profile_equivalence.py` (+ the 14th,
   candidate-resolved site), `test_pnl_scan.py`, `test_edge_report.py`, `test_setups.py`.
2. **6 files via I-8's explicit UPDATE table**: `test_mcp_server.py`, `test_meta_routes.py`,
   `test_copy_discipline.py` (verified via direct diff: the walked-surface list shrinks — the
   representative-served-copy leg sampling now-deleted taxonomy functions is dropped — the lint
   RULES/lexicon are untouched, T-7 satisfied), `test_research_api.py`, `test_research_store.py`,
   `test_studies_reference.py`.
3. **7 files as necessary, mechanical, correct consequences of I-2/I-5's `ResearchRegistry`
   deletions** (not itemized by filename in I-8, but directly required — the same "discovered gap,
   documented, fixed" pattern iter-1's own Known Issues already established under T-14):
   `test_backtests_api.py`, `test_bars_api.py`, `test_datasets_api.py`, `test_levels_api.py`,
   `test_setups_api.py`, `test_tradability_api.py` each drop 2-3 lines calling
   `manager.set_on_engine_created(registry.on_engine_created)` / `registry.study_jobs.join_all(...)`
   in their own fixture teardown — both target now-deleted `ResearchRegistry` members (I-2: "LOSES
   `study_jobs`, `on_engine_created`"; I-5: "DELETE `manager.set_on_engine_created(...)`). Left in
   place, these fixtures would raise `AttributeError` on every test run using them — the fix is
   mandatory, not optional. `test_observer_equivalence.py` drops exactly two whole test functions
   (`test_real_monitor_attached_outputs_byte_identical`,
   `test_real_monitor_with_thesis_does_not_alter_engine_outputs`) that imported the now-deleted
   `app.research.monitor.ResearchMonitor` and `store.ThesisRecord` — leaving them would be a
   `ModuleNotFoundError` at collection time (would have shown as a pytest ERROR, not merely FAIL).
   The file's OTHER, engine-frozen-foundation guard
   (`test_engine_is_research_agnostic_no_research_imports`) is untouched and still the most
   important test in that file.

**Frontend (6 files)**: `app/page.tsx` + `components/Cockpit.tsx` (I-7 cockpit thesis/hint/sound
integration removal), `lib/api.ts` (I-7, 14 functions removed, `fetchTaxonomy` kept),
`lib/types.ts` (I-7 type families removed), `components/PriceChart.tsx` (I-7/T-8 sanctioned chart
edit — see below), and **`app/structure/page.tsx` — THIS iteration's own edit** (the
`SHOW_CASE_STUDIES` flip + the one reinstated framing sentence; the only product file this
iteration touches, confirmed via `git diff --stat` showing exactly this one `apps/` file changed
since the last commit).

**Total: 11 + 25 + 4 + 11 (deletions) + 1 (addition) + 12 + 21 + 6 (modifications) = 91 — matches
the diff's total exactly. Zero residue.**

## Chart guard (veto-class, re-verified directly)

- `StructureChart.tsx`: `git diff e7865b4 --stat` is **empty** — zero bytes touched across the
  entire session. T-8 satisfied.
- `PriceChart.tsx`: full diff read line-by-line. The ENTIRE 107-line diff (25 insertions, 82
  deletions) is scoped to exactly one coherent change: removing the thesis-geometry overlay
  (the `thesis` prop, the `ThesisProjection` import, the `VERDICT_COLORS`/`PRICE_LINE_COLORS`/
  `MARK_COLOR` constants, and the `useMemo` blocks that built marker/price-line specs from the now
  -deleted WS `thesis.geometry` key — replaced with a stable `NO_PRICE_LINES` empty-array constant
  so the `extraPriceLines` seam stays wired without a fresh array per render) plus three comments
  updated to stop describing the removed behavior. No rendering logic, prop shape (beyond dropping
  `thesis`), or style changed. Matches I-7's chart clause verbatim.

## TC-17 — historical record check (re-verified this iteration, diffed against HEAD not baseline)

- `docs/goal-archive/`: `git diff HEAD --stat` empty (also empty vs the `e7865b4` baseline — never
  touched all session).
- `runs/goal-session-clean_slate/iter-0` through `iter-4`: `git diff HEAD --stat` empty AND
  `git status --short` empty — zero bytes changed since each was committed.
- `reports/pnl/pnl-history.md`: `git diff HEAD --stat` empty (untouched THIS iteration — no
  `pnl_baseline` re-run in J-05, correctly so per OUT OF SCOPE). Across the whole session
  (`e7865b4` → now) the file shows **15 insertions, 0 deletions** — purely additive (J-04's new
  epoch section appended beside the untouched old section, already audited PASS at iter-4).

## 14th derived-fingerprint pin site — re-confirmed by name

`tests/test_profile_equivalence.py::test_candidate_resolved_fingerprint_is_distinct_from_default`
re-run in isolation this iteration: **1 passed**. Source confirms it pins the CANDIDATE-PROFILE-
RESOLVED fingerprint literal `16d7c98e4fdca755` (distinct from the base pin `08e471b10130e1e2`,
which the adjacent `test_default_fingerprint_is_pinned_and_unmoved_by_the_new_field` independently
pins in the same file). Both literals stable, unchanged since iter-4.

## Two carried, pre-existing documentation-count observations (not new, not blocking)

Both are the same class of arithmetic slip iter-4's audit already found and closed elsewhere in
goal.md (its "13→14 pin sites" and "48→40 exclusion set" items) — flagged here only for completeness,
not as new findings requiring action:

1. **I-1's prose says "DELETE these 15 route handlers" but its own table enumerates only 14 rows.**
   iter-1's dev handoff already caught this at the time ("Deleted 14 route handlers... 404
   verified") and iter-1's review confirmed "14 routes deleted (404 verified)". This iteration's own
   live 404 sweep re-confirms: all 14 enumerated routes return exactly HTTP 404 today (`GET
   /research/analytics`, `/research/thesis/active`, `/research/hints/active`, `/research/hints`,
   `/research/journal`, `/research/journal/{id}`, `POST /research/thesis`, `POST
   /research/thesis/{id}/resolve`, `POST /research/thesis/{id}/action`, `POST
   /research/thesis/{id}/review`, `POST /research/studies`, `GET /research/studies`, `GET
   /research/studies/{id}`, `POST /research/studies/{id}/cancel`), and `GET /research/taxonomy`
   correctly still returns 200 (SLIM, not DELETE, T-5).
2. **I-8's DELETE list is prefixed "~24 files" but names 25.** The tilde already signals
   approximation in the source text; this iteration's diff shows exactly those 25 named test files
   deleted, name-for-name — not a real discrepancy.

## This iteration's own contribution (TC-15)

`git diff HEAD --stat -- apps/` (i.e. uncommitted changes on top of the last landed commit) shows
**exactly one file**: `apps/frontend/app/structure/page.tsx` (the `SHOW_CASE_STUDIES` flip +
the one reinstated framing sentence). No other `apps/` file is touched this iteration. New
non-`apps/` artifacts this iteration: this cross-check document, `kept-route-after.txt` (this
directory), the dev/frontend handoffs, the implementation summary, and `status.json` — all evidence
artifacts, not product code.
