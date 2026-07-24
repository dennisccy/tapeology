# Goal Iteration 6 — Demolition close-out: orphaned-model cleanup, source-introspection hardening, and J-05's final re-certification

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** clean_slate
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(This era's one sanctioned exception, operator-approved 2026-07-23: the journal/studies/performance product surfaces are REMOVED outright — never mutated-in-place — and their historical records stay readable; nothing else moves.)* *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **No research-value change beyond the documented epoch bump.** Every number a KEPT surface serves (levels, bands, touch events, edge cells, pnl rows) stays byte-identical on identical inputs; the ONLY sanctioned change is the `config_fingerprint` value itself, moved once via the J-04 Path B journey; cross-epoch pooling is forbidden forever. *(critical)*
  - **Deletion is complete, never cosmetic.** No orphaned imports, dead components, unreachable routes, dangling MCP tools, or skipped tests survive; a deleted surface is gone from code, routes, nav, MCP, types, and tests alike — grep-provably. *(critical)*
  - **No new features.** This era ships zero new product capabilities, pages, endpoints, strategies, or Config fields; anything new belongs to the next eras. *(critical)*
  - **Relocations are moves, not rewrites.** `r_basis` and the dataset-source constants keep byte-identical behaviour at their new homes; every kept caller's output is proven unchanged. *(critical)*
  - **Never modify the charts beyond the one named edit.** No commit in this era may edit `StructureChart.tsx` at all, or edit `PriceChart.tsx` beyond removing its thesis-geometry overlay build (I-7 chart clause); the three chart guard suites must pass byte-unmodified; any other chart diff — visual or behavioral — is a veto-class defect. *(critical)*
  - **Never touch a historical record.** No commit in this era may delete, rewrite, truncate, or re-stamp journal.db's existing rows or tables, any PnL-ledger row, anything under `docs/goal-archive/` or `runs/goal-session-*`, or any `reports/goal-session-*-delivered.md` — a diff touching any of these is a veto-class defect (deleting CODE is the mandate; deleting RECORDS is forbidden). *(critical)*
  - **No guard weakening.** `test_no_execution_path.py`, the source-introspection guards, and every kept test stay as written; the fingerprint pins change ONLY inside J-04 per Path B, never to make a red test green. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Delete the 5 grep-provable orphaned Pydantic request-body classes left in `routes.py` since iter-1, harden the codebase with a guard test so this defect class cannot silently recur, and re-certify — via an expanded orphan sweep, a fresh full-suite run, and a browser-verified regression pass — that J-05's "zero residue" completeness clause finally holds, closing the last open item of the interlude.

## BACKGROUND

Iter-5's hard audit — the one lane that caught what four lighter passes missed — found 5 orphaned Pydantic request-body classes (`ThesisRequest`/`ResolveRequest`/`ActionRequest`/`StudyRequest`/`ReviewRequest`, `routes.py:85/103/112/122/208`) still living in `routes.py` from iter-1's route demolition: each has exactly 1 grep occurrence (its own class-def line, zero live references) — a grep-provable MINOR breach of the critical-tagged "Deletion is complete, never cosmetic" anti-goal that blocks GOAL_ACHIEVED even though the classes are functionally inert (not in the OpenAPI schema, unimported). This planning pass independently re-confirmed the same 5 lines and separately swept for other orphans: the 4 KEPT request-body classes (`BacktestRequest`, `DatasetRecordRequest`, `BarRecordRequest`, `EdgeReportComputeRequest`) each occur twice in `routes.py` (def + a live `body:` route parameter), confirming the grep methodology is sound and finds nothing beyond the named 5; zero live (non-docstring) references remain anywhere in `apps/` to the deleted-module record dataclasses (`ThesisRecord`/`VerdictEventRecord`/`ActionRecord`/`StudyRecord`/`HintRecord`) or to `ResearchRegistry`'s removed members (`study_jobs`/`hint_projection_for`/`startup_sweep`); and `get_study_market_adapter` (`routes.py:318`) is confirmed a legitimate J-01 RELOCATION (its own docstring records the move; `record_dataset` is its live consumer) — **not** an orphan, and must not be touched. Frontend orphan types (`ThesisVerdict`/`Hint`/journal-study result types) are already grep-clean. Applying iter-5's own lesson ("the route 404s" is not the same as "the surface is gone from code, grep-provably" — a deletion audit must grep for orphaned request/response models and helper symbols, not only deleted-module imports, route 404s, MCP tool counts, and nav rows) and its explicit next-step recommendation, this iteration adds a durable source-introspection guard test (applying iter-2's lesson: build it structurally against the file's own current class/parameter shape, not by naming a deletion target, so it can't itself go stale later) and folds in the coherence advisory carried from iter-5 (README's 3 now-stale "withheld... pending an operator decision" sentences, lines ~51/55/56, left over from before iter-5 turned Case Studies back on). **Depth is `full`** per the prior evaluator's own explicit recommendation and the depth rubric's "hardening pass" + "requires new tests beyond browser smoke" triggers: the audit lane is the only lane that caught this residue across 4 prior passes, so it must independently re-certify the now-complete demolition before GOAL_ACHIEVED becomes evaluable; this is also the era-closing sentinel with veto-class chart requirements (T-8), so the full browser-qa/ux-regression/closure lanes apply. Target selection is unambiguous under the priority rubric: J-05 is the only non-passing journey and this iteration is its own closing work, not new scope (rule 3/4 — smallest remaining unblocker).

## IN SCOPE

### Backend
- [ ] Delete the 5 orphaned Pydantic request-body classes from `apps/backend/app/research/routes.py`: `ThesisRequest` (line 85), `ResolveRequest` (103), `ActionRequest` (112), `StudyRequest` (122), `ReviewRequest` (208) — class definitions and their docstrings only; no route, import, or other class is touched.
- [ ] Run the EXPANDED orphan sweep the audit called for: (a) grep every remaining `class X(BaseModel):` in `routes.py` and confirm each has ≥1 reference beyond its own def line; (b) grep the deleted-module record dataclass names (`ThesisRecord`, `VerdictEventRecord`, `ActionRecord`, `StudyRecord`, `HintRecord`) and `ResearchRegistry`'s removed members (`study_jobs`, `hint_projection_for`, `startup_sweep`) for any LIVE (non-docstring/non-comment) reference anywhere in `apps/`; (c) grep `apps/frontend/lib/types.ts`, `apps/frontend/lib/api.ts`, and `apps/frontend/app/` for the I-7 deleted type/function-family names. Confirm `get_study_market_adapter` (`routes.py:318`) is the J-01 RELOCATION and leave it untouched.
- [ ] Add ONE new source-introspection guard test (new file, e.g. `tests/test_routes_no_orphaned_request_models.py`) that enumerates every `class X(BaseModel):` defined in `app/research/routes.py` and asserts each is referenced by at least one live route-handler parameter in the same file — so a future route deletion that leaves its body-schema class behind fails this test immediately instead of surviving undetected.
- [ ] Re-run the full backend `pytest` suite fresh; confirm `0 failed`, and confirm `Config().config_fingerprint()` is unchanged at `08e471b10130e1e2` (this iteration touches zero `Config` fields — T-3 stays undisturbed).
- [ ] Re-run `test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, and the chart/source-introspection guard suites (`test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`, `test_price_chart_confluence.py`, the pinned guard blocks in `test_backtests.py` and `test_setups.py`) in isolation; confirm byte-identical file content vs. iter-5 (the only new file this iteration adds is the new guard test).
- [ ] Regenerate the session-wide diff-vs-inventory cross-check at `runs/goal-session-clean_slate/iter-6/diff-vs-inventory-crosscheck.md` (extending iter-5's cumulative-diff document), adding the newly-run orphaned-model grep results, this iteration's `routes.py` delta, and the one new guard-test file — confirm zero out-of-inventory changes.

### Frontend
- [ ] None — no `.tsx`/`.ts` file changes this iteration.

### Documentation
- [ ] Remove the 3 stale "currently withheld from view pending an operator decision" / "currently withheld from the Structure page pending an operator decision" clauses from `README.md` (lines ~51, 55, 56), rewording each surrounding sentence minimally so it accurately describes Case Studies as a rendered, reachable `/structure` section (matching the `SHOW_CASE_STUDIES=true` state iter-5 shipped) — no new claims beyond what iter-5's browser evidence already established.

### New user-facing capability
None. This is a dead-code-removal + hardening + documentation-accuracy iteration; the shipped product surface (Cockpit + Structure, both charts, Case Studies, Edge Report) is behaviorally and visually identical to iter-5's.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None. No rendered page, panel, or component changes.

### Product surface delta
Zero. Nav, page count, panel set, and every rendered value are unchanged; the entire delta is backend dead-code removal, one new backend guard test, and a documentation-prose correction.

### Blueprint conformance
No new surfaces. J-05's canonical homes (`/`, `/structure`) are unchanged in `blueprint.md`'s Information Architecture; no page, nav row, or Data-Contract owner is added, moved, or renamed this iteration — **no `blueprint.md` edit is required** (verified: no new displayed value, no new page, no nav change; `blueprint.reapproval-requested` is NOT written).

### Data-contract additions
None. No new endpoint, module, field, or displayed value is introduced; every value `/structure` and `/` already serve keeps its existing single owner exactly as registered in `blueprint.md`'s Data Contract table.

## OUT OF SCOPE

- Any new features, pages, endpoints, strategies, or Config fields (Non-Goal, verbatim).
- Any `Config` field deletion or fingerprint-pin edit — the pins moved ONCE, in J-04; this iteration touches zero pins and zero `Config` fields (T-3).
- Any engine change — `app/engine/` stays untouched.
- Any edit to `StructureChart.tsx`, or any `PriceChart.tsx` edit (T-8) — both stay 0-diff this iteration.
- Any edit to the 4 KEPT request-body classes (`BacktestRequest`, `DatasetRecordRequest`, `BarRecordRequest`, `EdgeReportComputeRequest`) or to `get_study_market_adapter` (a live J-01 relocation, not an orphan).
- Re-implementing or re-litigating J-01–J-04's own code — they stay `passing`, re-verified only.
- Re-shooting iter-5's already-evidenced full screenshot set from scratch; this iteration's browser pass confirms the (now-fuller) `journey-scripts/J-05.json` golden replay still holds and freshly confirms the Edge Report honest state, not a wholesale re-capture of every iter-5 screenshot.
- Any new data recording or live Yahoo/Alpaca fetch — the browser walk relies on already-persisted fixtures.
- Editing `docs/goal-archive/`, any prior `runs/goal-session-clean_slate/iter-*` directory, `reports/goal-session-*-delivered.md`, or any existing `reports/pnl/pnl-history.md` row.
- Any README edit beyond the 3 named stale sentences — no other prose rewrite, no unrelated "cleanup."

## DEFINITION OF DONE

- [ ] Target journey J-05 passes via browser-qa-agent (TC-9–TC-11).
- [ ] The 5 named orphaned classes are grep-provably gone (TC-1).
- [ ] The expanded orphan sweep reports zero additional orphaned request/response models or dead helper symbols, backend or frontend (TC-2, TC-3).
- [ ] The new source-introspection guard test passes and would have caught the just-fixed residue (TC-4).
- [ ] Full backend suite reports `0 failed`; `config_fingerprint()` unchanged at `08e471b10130e1e2` (TC-5, TC-6).
- [ ] Every guard/chart-guard suite passes byte-unmodified (TC-7).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04 remain `passing` (deterministic replay + LLM fallback — mechanically verified at both depths) (TC-8, TC-12, TC-13, TC-14).
- [ ] Session-wide diff-vs-inventory cross-check (iter-6) reports zero out-of-inventory changes (TC-15).
- [ ] The 3 stale README sentences are corrected (TC-16).
- [ ] No historical record touched (TC-17).
- [ ] No anti-goal violation introduced; the previously-unresolved MINOR violation ("Deletion is complete, never cosmetic") is fully resolved.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-clean_slate-iter-6-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (deterministic replay of `journey-scripts/J-05.json` — the fuller walk landed at iter-5: cockpit settle + timeframe switch + stop, `/structure` Load wall band, Case Studies drill-in — plus a fresh confirmatory screenshot of the Edge Report honest state, since this iteration's backend change lands in the same file (`routes.py`) that serves `/structure`'s other routes even though no live handler is touched). Regression smoke: LLM-fallback confirmatory touch of J-01/J-03/J-04's kept keyless surfaces (nav item count, MCP tool count, 404 sweep) since none has its own dedicated browser golden in this session (only J-02 and J-05 do).
- Unit/integration: full `pytest`; the new source-introspection guard test in isolation; the named guard/chart-guard files in isolation; a T-12-style import-grep sweep re-run for all 11 already-deleted modules; the I-1 404/200 sweep for the 14 deleted + 1 slimmed route; MCP `list_tools()` name/count check.
- Error cases: the new guard test's own logic must be shown to flag an unreferenced `BaseModel` (verified by inspecting that its assertion would have named any of the 5 just-deleted classes had they still been present — not merely that it passes today); each of the 14 fully-deleted I-1 routes must return exactly HTTP 404 (never 200 or a redirect); `GET /research/taxonomy` must return exactly HTTP 200 with the slimmed payload (feed_basis + source labels only, T-5).

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract
addition above maps to at least one concrete scenario line, numbered
sequentially, of exactly this shape:

- TC-1: given `apps/backend/app/research/routes.py` before this iteration contains `class ThesisRequest(BaseModel):` (line 85), `class ResolveRequest(BaseModel):` (103), `class ActionRequest(BaseModel):` (112), `class StudyRequest(BaseModel):` (122), and `class ReviewRequest(BaseModel):` (208), when the developer deletes all 5 class definitions, then `grep -c "class ThesisRequest\|class ResolveRequest\|class ActionRequest\|class StudyRequest\|class ReviewRequest" apps/backend/app/research/routes.py` returns `0`.
- TC-2: given every remaining `class X(BaseModel):` definition in `routes.py` after the deletion, when each class name is grepped for total occurrences within `routes.py`, then every remaining class shows 2 or more occurrences (its def line plus at least one live `body: X` route parameter) — zero remaining classes show exactly 1 occurrence.
- TC-3: given a grep restricted to `apps/` (excluding `reports/`, `runs/`, `docs/goal-archive/`) for the deleted-module record dataclass names (`ThesisRecord`, `VerdictEventRecord`, `ActionRecord`, `StudyRecord`, `HintRecord`) and the removed `ResearchRegistry` members (`study_jobs`, `hint_projection_for`, `startup_sweep`) as live code (excluding docstring/comment lines), when the sweep runs, then it returns zero hits, and a matching sweep of `apps/frontend/lib/types.ts`, `apps/frontend/lib/api.ts`, and `apps/frontend/app/` for the I-7 deleted type/function families also returns zero hits.
- TC-4: given the new guard test parses `app/research/routes.py` and enumerates every `class X(BaseModel):` alongside every route-handler parameter annotated with one of those classes, when the test runs against the current (post-cleanup) file, then it passes (the two sets are equal in size and membership) — and its assertion logic, re-applied to a copy of the pre-cleanup file content, names all 5 just-deleted classes as unreferenced.
- TC-5: given the backend on committed fixtures after this iteration's changes, when the full `pytest` suite is run fresh, then it reports `0 failed` and exits `0`.
- TC-6: given `Config().config_fingerprint()` computed live after this iteration's changes, when compared to the pre-iteration value, then it equals `08e471b10130e1e2` (unchanged).
- TC-7: given `test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, `test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`, `test_price_chart_confluence.py`, and the pinned guard blocks in `test_backtests.py`/`test_setups.py`, when each is re-run in isolation, then each passes AND `git diff` on those file contents is empty.
- TC-8: given a grep restricted to `apps/` for an import of any of the 11 already-deleted modules (`journal_rows`, `monitor`, `hints`, `stance`, `verdict`, `grades`, `marks`, `excursions`, `execution_checks`, `analytics`, `studies`), when run, then it returns zero hits.
- TC-9: given the frontend rebuilt fresh (`rm -rf apps/frontend/.next` per T-9) and the backend running, when the `journey-scripts/J-05.json` golden script replays, then every step passes: the cockpit shows "Buyer Control" text after watching `SIM-BUYER`, the tape-bar-size control switches to show the caption "Logical 30s bars built live from the tape.", "Stop watching" returns the page to "No ticker watched", `/structure` Load for AAPL as-of `2026-06-22T21:00:00Z` shows the text `300.11`, and clicking a `case-studies-row` element opens the `case-drillin` element.
- TC-10: given `/structure`'s Edge Report section in its current state, when the operator views it, then the panel shows either populated edge cells (a warm cache exists) or the exact text "Edge report not computed yet." alongside a visible Compute button — captured in a fresh screenshot.
- TC-11: given the top nav after the frontend rebuild, when the operator opens `/`, then it shows exactly two items — "Cockpit" and "Structure".
- TC-12: given the 14 fully-deleted I-1 routes (e.g., `GET /research/journal`, `GET /research/analytics`, `POST /research/studies`), when each is requested against the running backend, then every one returns HTTP 404, and `GET /research/taxonomy` returns HTTP 200 with the slimmed payload.
- TC-13: given the MCP server's `list_tools()`, when invoked, then it returns exactly the 15 I-6 tool names (no `journal`/`analytics`/`studies`).
- TC-14: given `apps/backend/tests/test_mcp_server.py`, `test_meta_routes.py`, and the 8 fingerprint-pin-site test files (I-9), when re-run in isolation, then each passes with zero content diff vs. iter-5.
- TC-15: given this iteration's cumulative diff (`runs/goal-session-clean_slate/iter-6/diff-vs-inventory-crosscheck.md`, extending iter-5's document) compared against I-1…I-9 + I-8's test dispositions + the newly-added guard test + this iteration's `routes.py` delta, when assembled, then it reports zero out-of-inventory changes.
- TC-16: given `README.md`'s 3 sentences (at approximately lines 51, 55, 56) containing "pending an operator decision" before this iteration, when this iteration's documentation fix lands, then `grep -c "pending an operator decision" README.md` returns `0`.
- TC-17: given `docs/goal-archive/`, every prior `runs/goal-session-clean_slate/iter-0` through `iter-5` directory, and `reports/pnl/pnl-history.md`'s pre-iteration-6 rows, when this iteration's diff is inspected, then none of those paths show a byte changed.

## NOTES

- **Lessons applied:** iter-5's lesson — a "complete-deletion" audit that greps only deleted-module imports, route 404s, MCP tool count, and nav rows misses orphaned request/response Pydantic models and helper functions; this iteration's Backend scope item 2 (the expanded sweep) and item 3 (the new guard test) are direct responses. iter-2's lesson — a source-introspection guard test can silently break when it names a deletion target by string; the new guard test instead asserts a structural invariant (every `BaseModel` in `routes.py` is referenced by a live route parameter) so it stays meaningful regardless of future deletions and cannot itself go stale.
- **Planning-time verification trail** (so the developer starts from confirmed ground truth, not a re-discovery): `grep -n "^class .*BaseModel" apps/backend/app/research/routes.py` lists 9 classes total; `ThesisRequest`/`ResolveRequest`/`ActionRequest`/`StudyRequest`/`ReviewRequest` each occur exactly once (their own def line); `BacktestRequest`/`DatasetRecordRequest`/`BarRecordRequest`/`EdgeReportComputeRequest` each occur exactly twice (def + a live `body:` parameter). A grep for `study_jobs`, `hint_projection_for`, `startup_sweep`, `ThesisRecord`, `VerdictEventRecord`, `ActionRecord`, `StudyRecord`, `HintRecord` across `apps/` (excluding `reports/`, `runs/`, `docs/goal-archive/`) returns only docstring/comment hits describing their historical removal — zero live references. `get_study_market_adapter` (`routes.py:318`) is a genuine J-01 RELOCATION (its own docstring: "era-5D J-01: relocated here... from beside the now-deleted `POST /research/studies` route... A pure move: same name, same body, same behaviour") with a live consumer (`record_dataset`) — flagging this explicitly so it is **not** mistaken for a 6th orphan and deleted by name-similarity (T-1-class trap). Frontend grep for `ThesisVerdict`/`ThesisStatement`/`ThesisMarks`/`ThesisGeometry`/`ThesisProjection`/`Hint`/journal-analytics-study result types across `lib/` and `app/` returns zero hits already.
- **README fix location:** the 3 stale sentences are in the Structure-page bullet (~line 51) and the two research-API/recording-tool bullets (~lines 55–56) of `README.md`'s feature list — all three currently read "...but it is currently withheld from view pending an operator decision..." / "...but it is currently withheld from the Structure page pending an operator decision..." / "...which is currently withheld from the Structure page pending an operator decision...". Reword each minimally to state the section renders; do not touch any other README content (the "Chart timeframe" bullet iter-5 already added is out of scope here).
- If this iteration's evidence is clean (J-05 passing, J-01–J-04 still passing, zero regression, zero anti-goal violation, session-wide diff-vs-inventory cross-check clean), all 5 Must-have journeys of this interlude are `passing`. Whether that constitutes `GOAL_ACHIEVED` is the evaluator's determination alone, per the deterministic-gates + two-key confirm protocol — this spec does not presume it.
