# goal-clean_slate-iter-6 Execution Plan

Interlude "The Clean Slate," closing iteration. Target journey: J-05 (regression sentinel) only.
Required-still-passing: J-01–J-04. This is a cleanup + hardening + re-certification pass triggered
by iter-5's own hard-audit finding (B1) — it adds zero new product capability.

## What to Build

- Delete the 5 grep-provable orphaned Pydantic request-body classes left in
  `apps/backend/app/research/routes.py` since iter-1's route demolition: `ThesisRequest` (L85),
  `ResolveRequest` (L103), `ActionRequest` (L112), `StudyRequest` (L122), `ReviewRequest` (L208) —
  class definitions + docstrings only, nothing else in the file.
- Run the expanded orphan sweep the iter-5 audit called for: (a) confirm every remaining
  `class X(BaseModel)` in `routes.py` shows ≥2 occurrences (def + a live `body:` route param); (b)
  confirm zero live (non-docstring) references anywhere in `apps/` to the deleted-module record
  dataclasses (`ThesisRecord`, `VerdictEventRecord`, `ActionRecord`, `StudyRecord`, `HintRecord`) or
  to `ResearchRegistry`'s removed members (`study_jobs`, `hint_projection_for`, `startup_sweep`);
  (c) same zero-hit sweep in `apps/frontend/lib/types.ts`, `lib/api.ts`, `app/` for the I-7 deleted
  type/function families. Confirm `get_study_market_adapter` (`routes.py:318`) is untouched — it is
  a genuine J-01 relocation with a live consumer (`record_dataset`), not a 6th orphan.
- Add ONE new source-introspection guard test,
  `apps/backend/tests/test_routes_no_orphaned_request_models.py`: enumerate every
  `class X(BaseModel):` defined in `routes.py` and assert each is referenced by at least one live
  route-handler parameter in the same file. Build it **structurally** (parse the file's own current
  shape), never by naming the 5 deleted classes as strings — that's iter-2's carried lesson, so the
  test can't itself go stale after a future deletion.
- Full fresh `pytest` run: 0 failed; live `Config().config_fingerprint()` unchanged at
  `08e471b10130e1e2` (this iteration touches zero `Config` fields/pins).
- Re-run in isolation, confirm `git diff` empty on each: `test_no_execution_path.py`,
  `test_no_credential_in_artifacts.py`, the 3 chart-guard suites (`test_cockpit_chart_upgrade.py`,
  `test_structure_chart_viewport.py`, `test_price_chart_confluence.py`), the pinned guard blocks in
  `test_backtests.py`/`test_setups.py`, `test_mcp_server.py`, `test_meta_routes.py`, the 8
  fingerprint-pin-site test files not already in that list.
- Regenerate `runs/goal-session-clean_slate/iter-6/diff-vs-inventory-crosscheck.md`, extending
  iter-5's version (already at `runs/goal-session-clean_slate/iter-5/diff-vs-inventory-crosscheck.md`
  — read it first), adding this iteration's orphan-sweep results + `routes.py` delta + the one new
  test file; confirm zero out-of-inventory changes.
- README.md: verify only (see Assumptions — already satisfied at planning time).
- Browser regression pass (after `rm -rf apps/frontend/.next` rebuild, T-9): replay
  `runs/goal-session-clean_slate/journey-scripts/J-05.json` (already exists from iter-5) plus a fresh
  screenshot of the Edge Report's current honest state; LLM-fallback confirmatory touch of J-01/J-03/
  J-04's keyless surfaces (nav item count, MCP tool count, 404 sweep).

## Agents Required

- backend-data: yes -- delete the 5 orphaned classes, run the expanded grep sweep, add the new
  structural guard test, re-run the full suite + isolated guard/chart-guard files, regenerate the
  diff-vs-inventory crosscheck, verify (and only if actually needed) the README wording. All
  backend-only work, dispatched to the standard `developer` agent.
- frontend-ux: no -- zero `.tsx`/`.ts` files change this iteration; both charts (`StructureChart.tsx`,
  `PriceChart.tsx`) and all other frontend code stay byte-unmodified (T-8, veto-class if violated).
  The mandatory browser walk below is QA/evidence work, not new frontend development.

## Frontend Present
yes

(Mandated by the phase's own metadata and by T-13 — "no screenshot ⇒ unknown, never passing" — even
though no frontend file changes: J-05 is a browser-verified regression sentinel over the already-
shipped two-page product. QA must still run the full Chrome MCP walk.)

## Files to Create/Modify

- `apps/backend/app/research/routes.py` -- delete exactly 5 classes (`ThesisRequest`,
  `ResolveRequest`, `ActionRequest`, `StudyRequest`, `ReviewRequest` + their docstrings). Nothing
  else in this file changes — the 4 kept classes (`BacktestRequest`, `DatasetRecordRequest`,
  `BarRecordRequest`, `EdgeReportComputeRequest`) and `get_study_market_adapter` (L318) are untouched.
- `apps/backend/tests/test_routes_no_orphaned_request_models.py` -- NEW structural guard test.
- `runs/goal-session-clean_slate/iter-6/diff-vs-inventory-crosscheck.md` -- NEW, extends iter-5's.
- `README.md` -- verify-only; edit lines ~51/55/56 ONLY if the grep in TC-16 still finds "pending an
  operator decision" (planning-time read found it already clean — see Assumptions).
- `docs/handoffs/goal-clean_slate-iter-6-dev.md` -- dev handoff (required by DoD).

No other file should change this iteration: zero `Config` fields, zero fingerprint-pin edits, zero
`app/engine/` changes, zero `.tsx`/`.ts` changes.

## UI Evolution
- New user-facing capability: none.
- New information displayed: none.
- New user actions: none.
- UI surface changes: none — 0 frontend files touched; nav stays exactly Cockpit/Structure.
- Navigation changes: none.

## Visual Requirements
- Component patterns: N/A — no new UI this iteration; re-confirm existing patterns render unchanged
  (Case Studies table + row-click drill-in, Edge Report panel/Compute button, StructureChart band
  overlay, PriceChart live tape bars).
- Layout: unchanged.
- Key visual effects: none new.
- States to handle: re-confirmation only — Edge Report's honest "Edge report not computed yet." (or
  populated cells) state, Case Studies drill-in open state, nav showing exactly 2 items.

## Key Test Scenarios

- TC-1/TC-2: grep confirms the 5 named classes are gone from `routes.py`; every remaining
  `class X(BaseModel)` shows ≥2 occurrences (def + live `body:` param) — zero classes left at exactly
  1 occurrence.
- TC-3 (+ T-12 style sweep): zero live refs anywhere in `apps/` to the 5 deleted-module record
  dataclasses or the 3 removed `ResearchRegistry` members; same zero-hit result for the I-7 deleted
  frontend type/function families. `get_study_market_adapter` confirmed untouched — a real relocation,
  not an orphan (name-similarity trap per goal.md's Notes).
- TC-4: the new guard test passes today, AND its own logic — reapplied to the pre-cleanup file
  content — would have named all 5 just-deleted classes as unreferenced. Must be structural (parses
  the file's current class/param shape), never a hardcoded name list.
- TC-5/TC-6: full fresh `pytest` = 0 failed, exit 0; `Config().config_fingerprint()` unchanged —
  live-verified at planning time as `08e471b10130e1e2`, matching the spec's expectation exactly.
- TC-7/TC-8/TC-14: the guard/chart-guard/MCP/meta/fingerprint-pin test files all pass in isolation
  AND `git diff` on each is empty.
- TC-9/TC-10/TC-11: after the clean `.next` rebuild (T-9), the `journey-scripts/J-05.json` golden
  replay passes every step; a fresh screenshot captures the Edge Report's current honest state; the
  top nav shows exactly "Cockpit" and "Structure".
- TC-12/TC-13: all 14 fully-deleted I-1 routes return 404, `GET /research/taxonomy` returns 200 with
  the slimmed payload; MCP `list_tools()` returns exactly the 15 I-6 tool names.
- TC-15: the iter-6 diff-vs-inventory crosscheck (extending iter-5's) reports zero out-of-inventory
  changes.
- TC-16: `grep -c "pending an operator decision" README.md` returns `0` — **already true today**
  (see Assumptions); run the grep first, only edit if it's non-zero.
- TC-17: zero bytes changed under `docs/goal-archive/`, `runs/goal-session-clean_slate/iter-0`
  through `iter-5`, and `reports/pnl/pnl-history.md`'s pre-iteration-6 rows.

## Assumptions / Planning Notes

- **README fix already satisfied.** A direct read of the full current `README.md` (158 lines) found
  ZERO occurrences of "pending an operator decision" anywhere in the file — the 3 sentences the spec
  names (~lines 51/55/56, inside the `AUTO:capabilities` block) already read as accurate, complete
  descriptions of Case Studies and the Edge Report as rendered, reachable `/structure` sections. This
  is almost certainly because `readme-maintainer` already regenerated `AUTO:capabilities` after
  iter-5 shipped the `SHOW_CASE_STUDIES` flip. **Developer action:** run TC-16's grep FIRST; if it
  already returns 0, record that as "verified, no edit needed" in the handoff rather than rewriting
  already-correct AUTO-block prose (an unforced edit risks drifting from `readme-maintainer`'s format
  and isn't what TC-16 requires — TC-16 only requires the grep to return 0, which it already does).
- **Fingerprint pre-verified.** Live-computed `Config().config_fingerprint()` on the current tree
  already reads `08e471b10130e1e2` (matches TC-6). Zero `Config` fields change this iteration, so it
  should stay exactly there — any drift is an immediate stop-the-line signal (T-3).
- **9 total `BaseModel` classes exist in `routes.py` today** (directly grep-confirmed): the 5 to
  delete plus the 4 to keep untouched (`BacktestRequest`, `DatasetRecordRequest`, `BarRecordRequest`,
  `EdgeReportComputeRequest`). Exactly 4 should remain after deletion, and the new guard test should
  assert all 4 are referenced.
- **No spec/goal drift.** This iteration is squarely inside the interlude's own mandate — it is the
  audit-recommended cleanup of iter-5's own finding (B1), not new scope, and it maps cleanly onto the
  "Deletion is complete, never cosmetic" and "No new features" rails in `docs/goal.md`. Nothing here
  touches `app/engine/`, either chart component, any `Config` field, or any fingerprint pin. No
  out-of-scope items to flag.
- **Do not touch:** the 4 kept `*Request` classes; `get_study_market_adapter` (a genuine relocation,
  not an orphan — do not delete by name-similarity); any of the 13 fingerprint pin-assertion lines
  (pins are frozen outside J-04, already closed); `StructureChart.tsx`; `PriceChart.tsx`;
  `app/engine/`.
- A frontend dev handoff (`docs/handoffs/goal-clean_slate-iter-6-frontend.md`) is likely unnecessary
  this iteration since the expected frontend diff is zero — only skip it if the diff is truly empty
  at handoff time.
