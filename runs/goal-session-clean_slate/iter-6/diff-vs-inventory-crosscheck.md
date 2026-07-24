# J-05 session-wide diff-vs-inventory cross-check — iteration 6 (extends iter-5's)

**Scope:** extends `runs/goal-session-clean_slate/iter-5/diff-vs-inventory-crosscheck.md` verbatim
(that document's own findings are unchanged and not re-litigated here). This document adds
iteration 6's own contribution: the orphaned-request-model cleanup, the new structural guard test,
and the expanded orphan sweep the iter-5 hard audit called for (finding B1). Commands:
`git diff e7865b4 --stat -- apps/` (cumulative, since the session baseline) and
`git diff HEAD --stat` (this iteration's own uncommitted contribution on top of the already-landed
iter-0..5 work at `ca5a663`).

**Result: this iteration's own diff is exactly ONE tracked-file modification
(`apps/backend/app/research/routes.py`, 67 deletions, 0 insertions) plus ONE new untracked test
file (`apps/backend/tests/test_routes_no_orphaned_request_models.py`). Zero out-of-inventory
changes found.**

## This iteration's own contribution (uncommitted, `git diff HEAD`)

| File | Change | Inventory row |
|---|---|---|
| `apps/backend/app/research/routes.py` | 67 lines deleted, 0 inserted | Backend scope item 1 — deletes the 5 orphaned Pydantic request-body classes (`ThesisRequest`, `ResolveRequest`, `ActionRequest`, `StudyRequest`, `ReviewRequest`) left behind by J-01's route demolition. Class definitions + docstrings only; the blank-line convention (2 blank lines between top-level defs) is preserved on both sides of each deletion so the diff is a pure subtraction. |
| `apps/backend/tests/test_routes_no_orphaned_request_models.py` | new file (152 lines) | Backend scope item 3 — the new source-introspection guard test (structural, parses `routes.py`'s own AST; never names a class as a string). |

No other file changed this iteration. (`runs/goal-session-clean_slate/telemetry.jsonl` and
`runs/goal-session-clean_slate/trace/trace.jsonl` show pipeline-engine instrumentation writes —
not product code, not `apps/`, not part of this cross-check's scope.)

## TC-1 — the 5 named classes are grep-provably gone

```
$ grep -c "class ThesisRequest\|class ResolveRequest\|class ActionRequest\|class StudyRequest\|class ReviewRequest" apps/backend/app/research/routes.py
0
```

## TC-2 — every remaining `class X(BaseModel):` in `routes.py` shows ≥2 occurrences

```
BacktestRequest:          2  (def + `body: BacktestRequest` at the /research/backtests route)
DatasetRecordRequest:     2  (def + `body: DatasetRecordRequest` at the /research/datasets route)
BarRecordRequest:         2  (def + `body: BarRecordRequest` at the /research/bars route)
EdgeReportComputeRequest: 2  (def + `body: EdgeReportComputeRequest` at the compute-trigger route)
```

Exactly 4 `BaseModel` classes remain (9 before this iteration, matching the plan's pre-verified
count) — zero at exactly 1 occurrence.

## TC-3 — expanded orphan sweep: zero live references anywhere in `apps/`

**(a) Deleted-module record dataclasses + removed `ResearchRegistry` members** — grepped for
`ThesisRecord`, `VerdictEventRecord`, `ActionRecord`, `StudyRecord`, `HintRecord`, `study_jobs`,
`hint_projection_for`, `startup_sweep` across `apps/` (all `.py` files):

| File | Line | Content | Classification |
|---|---|---|---|
| `apps/backend/tests/test_research_store.py` | 5-6 | module docstring: "...along with the deleted `JournalStore` methods and record dataclasses (`ThesisRecord`, `ActionRecord`, `VerdictEventRecord` — I-3)..." | historical documentation comment, not live code |
| `apps/backend/app/main.py` | 150 | comment: "`ResearchRegistry.on_engine_created`/`.startup_sweep`)." | historical documentation comment, not live code |
| `apps/backend/app/research/edge_report.py` | 40 | docstring: "...`ThesisRecord.risk_flags`)..." | historical documentation comment, not live code |
| `apps/backend/app/research/routes.py` | 160 | `ResearchRegistry`'s own class docstring describing J-01/J-02's removals, including `hint_projection_for` | historical documentation comment, not live code |

All 4 hits are comments/docstrings narrating what was already removed — zero live (executable)
references. Matches T-11's "history in prose is not a live reference" discipline.

**(b) Frontend I-7 deleted type/function families** — grepped `apps/frontend/lib/types.ts`,
`apps/frontend/lib/api.ts`, `apps/frontend/app/`, `apps/frontend/components/` for the 11 deleted
component names, the 14 deleted `api.ts` functions, and the deleted `types.ts` families
(`ThesisVerdict`, `ThesisStatement`, `ThesisMarks`, `ThesisGeometry`, `ThesisProjection`):

- api.ts function names: **zero hits**.
- types.ts family names: **zero hits**.
- Component names: **one hit** — `apps/frontend/app/structure/page.tsx:1305`, a `//` code comment
  on `BacktestPanel` explaining a design choice ("...so this is intentionally NOT a reuse of
  `StudyResultsView`'s `results-cancelled` copy."). Read in context (lines 1301-1306): pure
  prose inside a comment block, not an import, JSX usage, or any live reference to the deleted
  component. Classified the same as the backend docstring hits above — historical rationale, not
  a dangling reference requiring cleanup.

**(c) `get_study_market_adapter` (`routes.py`, now at line 251 after this iteration's deletions)**
— re-confirmed a genuine J-01 RELOCATION, not a 6th orphan: its own docstring states "era-5D J-01:
relocated here (this file's dataset-routes section) from beside the now-deleted `POST
/research/studies` route, its ORIGINAL sole other caller — `record_dataset` below is now its only
consumer. A pure move: same name, same body, same behaviour." Grep confirms exactly one live call
site (`adapter = get_study_market_adapter()` inside `record_dataset`) plus two docstring
cross-references elsewhere in the file describing the relationship. Untouched this iteration, as
required.

## TC-4 — the new guard test's logic is proven sound, not merely passing today

`apps/backend/tests/test_routes_no_orphaned_request_models.py` parses `routes.py`'s AST
structurally (collects every top-level `class X(BaseModel):`, then every function-parameter
annotation naming a class, anywhere in the file) — it never hardcodes a class name as a string, so
it stays meaningful after any future deletion.

- Run against the file BEFORE this iteration's deletions (captured live at the start of this
  iteration): **FAILED**, naming exactly `['ActionRequest', 'ResolveRequest', 'ReviewRequest',
  'StudyRequest', 'ThesisRequest']` as orphans — proving the guard would have caught this defect
  had it existed sooner.
- A second test in the same file (`test_the_guard_would_have_flagged_the_just_deleted_orphans_pre_cleanup`)
  re-applies the identical structural logic to a small synthetic module reproducing the pre-cleanup
  shape and asserts it names exactly those 5 classes — a permanent, self-contained proof of the
  guard's own soundness that does not depend on `routes.py`'s current state.
- Run against the file AFTER this iteration's deletions: **PASSED** (both tests).

## TC-5 / TC-6 — full suite + fingerprint

```
$ .venv/bin/python -m pytest tests/
1169 passed, 7 skipped, 2 warnings in 122.51s

$ .venv/bin/python -c "from app.config import Config; print(Config().config_fingerprint())"
08e471b10130e1e2
```

0 failed; fingerprint unchanged from the pre-iteration value (`08e471b10130e1e2`) — this iteration
touches zero `Config` fields and zero fingerprint pins (T-3 undisturbed).

## TC-7 / TC-8 / TC-14 — guard / chart-guard / MCP / meta / fingerprint-pin files: unmodified AND green

`git diff HEAD --stat` on each of the following is empty (byte-identical to the already-landed
iter-5 state), and all pass when re-run in isolation together (354 passed, 0 failed, 46.34s):

`test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, `test_cockpit_chart_upgrade.py`,
`test_structure_chart_viewport.py`, `test_price_chart_confluence.py`, `test_backtests.py`,
`test_setups.py`, `test_mcp_server.py`, `test_meta_routes.py`, `test_timeframe_history_api.py`,
`test_levels.py`, `test_tradability.py`, `test_profile_equivalence.py`, `test_pnl_scan.py`,
`test_edge_report.py` — the last 8 in this list are exactly the 8 files hosting I-9's 13
fingerprint-pin assertion sites.

T-12-style import-grep re-run for all 11 already-deleted modules (`journal_rows`, `monitor`,
`hints`, `stance`, `verdict`, `grades`, `marks`, `excursions`, `execution_checks`, `analytics`,
`studies`): zero import hits, and all 11 module files are confirmed physically absent from
`apps/backend/app/research/`.

## Chart guard (veto-class, re-confirmed unchanged this iteration)

- `StructureChart.tsx`: `git diff HEAD --stat` empty. `git diff e7865b4 --stat` empty (zero bytes
  touched all session, unchanged from iter-5's finding). T-8 satisfied.
- `PriceChart.tsx`: `git diff HEAD --stat` empty this iteration (iter-5's already-audited chart
  edit — the thesis-geometry overlay removal — is the session's only diff, unchanged).

## Live keyless re-verification (this iteration, backend running on committed fixtures)

- All 14 fully-deleted I-1 routes return exactly HTTP 404 (`GET /research/analytics`,
  `/research/thesis/active`, `/research/hints/active`, `/research/hints`, `/research/journal`,
  `/research/journal/{id}`, `POST /research/thesis`, `POST /research/thesis/{id}/resolve`, `POST
  /research/thesis/{id}/action`, `POST /research/thesis/{id}/review`, `POST /research/studies`,
  `GET /research/studies`, `GET /research/studies/{id}`, `POST /research/studies/{id}/cancel`).
- `GET /research/taxonomy` returns HTTP 200 with exactly the slimmed payload: `feed_basis.feeds`
  (sim/iex/sip/yahoo) + `live_disclosure` — no thesis/verdict/stance/study label families.
- MCP `list_tools()` returns exactly 15 tools, name-for-name matching I-6:
  `tape_state`, `tape_features`, `tape_history`, `datasets`, `bars`, `levels`, `tradability`,
  `setups`, `backtests`, `strategies`, `pnl_ledger`, `taxonomy`, `edge_report`, `ui_route_map`,
  `get_endpoint`.
- Frontend confirmatory sweep (dev server on :3301, no `.next` rebuild needed since zero frontend
  files changed this iteration): `/` → 200, `/structure` → 200, `/journal` → 404, `/studies` → 404,
  `/performance` → 404. Both backend and frontend started cleanly with no errors in their logs, then
  were stopped (dev-verification only — the full browser-evidenced walk with screenshots is QA's
  pass, per this iteration's own plan: "The mandatory browser walk below is QA/evidence work, not
  new frontend development").

## TC-16 — README already clean, no edit needed

`grep -c "pending an operator decision" README.md` → `0` (verified BEFORE any change this
iteration, and unchanged after — the file was not edited). Matches the plan's own planning-time
finding: `readme-maintainer` had already regenerated the `AUTO:capabilities` block after iter-5
shipped `SHOW_CASE_STUDIES=true`, so the 3 stale sentences the goal spec named no longer exist in
the file. No edit was made (an unforced edit to already-correct AUTO-block prose was correctly
avoided, per the plan's own explicit guidance).

## TC-17 — historical record check (re-verified this iteration)

- `docs/goal-archive/`: `git diff HEAD --stat` empty; `git diff e7865b4 --stat` empty (untouched
  all session).
- `runs/goal-session-clean_slate/iter-0` through `iter-5`: `git diff HEAD --stat` empty AND `git
  status --short` empty for each — zero bytes changed since each was committed.
- `reports/pnl/pnl-history.md`: `git diff HEAD --stat` empty (untouched this iteration — correctly
  so, since J-04's epoch bump is not re-run here).

## Cumulative session diff (vs. `e7865b4`, the pre-iter-0 baseline) — unchanged in file-count terms

```
$ git diff e7865b4 --name-status -- apps/ | awk '{print $1}' | sort | uniq -c
      1 A
     51 D
     39 M
```

Still 91 tracked-file changes (1 added, 51 deleted, 39 modified) — identical to iter-5's own
reported total, because this iteration's `routes.py` edit lands inside a file that was already
counted as modified (`M`) in that total; it does not add a new row. `routes.py`'s own cumulative
delta vs. the baseline is now **57 insertions, 1230 deletions** (up from whatever iter-1..5 had
already removed — this iteration's own 67-line contribution is included in that total, confirmed
separately above under "This iteration's own contribution"). The new guard test file is currently
**untracked** (not yet part of any commit), so it does not appear in a `git diff <commit>` count
against a commit; once committed it will be session addition #2 (alongside J-04's
`test_fingerprint_epoch_retirement.py`), bringing the cumulative total to 92 files.

## Conclusion

Every change this iteration maps to exactly one Backend scope item from the phase spec (delete 5
orphaned classes; run the expanded orphan sweep; add the one new guard test). Nothing outside the
plan's declared scope was touched. Zero out-of-inventory changes found. The previously-unresolved
MINOR anti-goal breach ("Deletion is complete, never cosmetic" — the 5 orphaned classes) is fully
resolved and now durably guarded against recurrence.
