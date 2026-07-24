# goal-clean_slate-iter-2 Execution Plan

Session `clean_slate`, iteration 2, depth **full**, Mode **next**. Target journey **J-02** ("Frontend +
WS demolition — the two-page product") — the second of five Must-have journeys in "The Clean Slate"
demolition interlude (`docs/goal.md`). Required-still-passing: **J-01** (keyless, re-verified via the
I-9 byte-comparison re-capture, not a browser replay) and **J-05** (its browser-walkable subset that
this iteration's own diff touches only — both charts, provenance badge, sim cockpit flow; J-05's other
clauses — Case Studies, full-suite-under-new-pin, cumulative diff-vs-inventory — depend on J-04 and stay
out of scope). Full acceptance detail, the I-1..I-9 inventory, Weak-model traps T-1..T-14, and the
TC-1..TC-18 test-first contract live in `docs/phases/goal-clean_slate-iter-2.md` — the developer must
read it in full. This plan distills it into an execution order; it is a guide, not a restatement.

**Alignment check:** J-02 is goal.md's own next journey in the J-01→J-02→J-03→J-04→J-05 dependency
order, and iter-1's audit explicitly recommended it next (`docs/handoffs/goal-clean_slate-iter-1-audit.md`
§5). Iter-1 (J-01) deleted the 14 backend routes / 11 modules and left `apps/frontend/` byte-untouched
(`git diff apps/frontend/` empty, confirmed in the iter-1 dev handoff) — so this iteration is the first
one to touch the frontend, and it can now safely delete the frontend code that CALLS those routes
because they are already gone. I independently re-verified the load-bearing anchors this phase spec
depends on directly against the current repo (not just trusting the spec's own claims): the WS merge
(`app/main.py:595,600,607,619` — `frame["thesis"]`/`frame["hint"]` assignments + both projection
helpers), the four `ResearchRegistry` stubs (`app/research/routes.py:237,266,269,283,294`), `app/meta.py`'s
`UI_ROUTES` tuple (journal/studies/performance rows at lines 26/28/29), all 3 frontend pages and all 11
components (still present), all 14 doomed `lib/api.ts` functions plus the kept `fetchTaxonomy`, the
`onHintDeclare`/`Hint` wiring in `Cockpit.tsx`, the `thesis`/`ThesisProjection`/`thesisSpecs` block in
`PriceChart.tsx`, the thesis/hint type families and `TapeSnapshot.thesis?`/`.hint?` fields in
`lib/types.ts`, `NavBar.tsx`'s dynamic (no-hardcoded-list) `/meta/ui-routes` fetch, and
`test_meta_routes.py`'s current 6 test names — every one matches the phase spec's claims exactly, zero
drift found. No scope creep: this phase ships zero new features/pages/endpoints/Config fields — it is a
pure subtractive delta plus one mechanical rewiring (severing the WS thesis/hint merge), matching
goal.md's Non-Goals verbatim.

**Note on `lib/useTapeStream.ts`:** the phase spec's IN-SCOPE line lists this file for updating (its
frame type "drops `thesis`/`hint`"), but I found zero references to `thesis`/`hint` by name inside it —
it appears to consume `TapeSnapshot` structurally without destructuring those keys. It may need **no
direct edit** once `lib/types.ts` drops the optional fields; verify with `tsc --noEmit` (TC-10) rather
than assuming an edit is required. Not a gap, just a heads-up so this isn't mistaken for a missed file.

## What to Build

Ordered so T-9's clean rebuild sits strictly after all code edits and strictly before any browser
verification. Re-verify every anchor by symbol/grep before editing, not by the line numbers below
(files shift as earlier steps land — same discipline iter-1 used).

**Backend**
1. `app/main.py` — delete `frame["thesis"] = _thesis_projection(ticker)` / `frame["hint"] =
   _hint_projection(ticker)` and both helper functions. The WS frame becomes the engine projection only.
2. **Same commit as #1** — `app/research/routes.py`: delete `ResearchRegistry`'s now-genuinely-dead stub
   surface — the `_monitors` dict and `monitor_for`/`projection_for`/`_surviving_projection`/
   `hint_projection_for` — their only caller was the WS merge just removed. Update the class docstring
   (it currently justifies their existence by that caller). This closes iter-1's own carried-forward gap
   (dev handoff Known Issue #4 / audit finding B2) — do it in the same commit as #1, not a separate one.
3. `app/meta.py` — trim `UI_ROUTES` to exactly the Cockpit (`/`) and Structure (`/structure`) rows.
   Do **not** hand-edit `NavBar.tsx` or `TopBar.tsx` — neither has a hardcoded route list; the nav
   shrinks automatically from the `GET /meta/ui-routes` response.
4. `tests/test_meta_routes.py` — update `test_ui_routes_lists_exactly_the_live_routes` and
   `test_ui_routes_top_bar_entries_match_the_rendered_nav_set` to the 2-row payload; delete
   `test_ui_routes_includes_performance_now_its_page_ships` and
   `test_ui_routes_represents_journal_detail_honestly` (they assert routes that no longer exist); leave
   `test_ui_routes_every_entry_carries_path_and_label` and `test_ui_routes_includes_structure_now_its_page_ships`
   unchanged.

**Frontend**
5. Delete pages `apps/frontend/app/journal/` (incl. `[id]/`), `app/studies/`, `app/performance/`.
6. Delete the 11 components: `JournalTable`, `JournalDetailView`, `JournalFilterBar`, `ThesisStrip`,
   `HintDock`, `HintLog`, `SoundCue`, `StudyList`, `StudyCreateForm`, `StudyResultsView`, `AnalyticsView`.
7. `lib/api.ts` — delete the 14 named functions (`declareThesis`, `resolveThesis`, `recordAction`,
   `saveReview`, `fetchActiveThesis`, `fetchActiveHint`, `fetchHints`, `fetchJournal`,
   `fetchJournalDetail`, `fetchAnalytics`, `createStudy`, `fetchStudies`, `fetchStudy`, `cancelStudy`).
   `fetchTaxonomy` stays — `FeedBasisBadge.tsx` is its only caller.
8. `lib/types.ts` — delete the thesis/hint/journal/study/analytics type families (`ThesisVerdict`,
   `ThesisStatement`, `ThesisMarks`, `ThesisGeometry`, `ThesisProjection`, `Hint`, `HintsTaxonomy`,
   `ThesisGrades`, `ThesisExcursions`, the journal-detail/study/analytics result types); slim
   `ResearchTaxonomy` to feed_basis + source labels; drop `thesis?`/`hint?` from `TapeSnapshot`.
9. `lib/useTapeStream.ts` — check whether any edit is actually needed after #8 (see note above);
   confirm via `tsc --noEmit`.
10. `app/page.tsx` — remove the thesis/hint integration in full: the `fetchActiveThesis` import, the
    `Hint`/`ThesisProjection`/`ThesisStrip`/`ThesisPrefill` imports, `survivingThesis` state and its
    post-Stop `GET /research/thesis/active` read inside `handleStop`, `hintPrefill`/`handleHintDeclare`,
    both `<ThesisStrip>` render sites (the live one and the post-stop "surviving thesis" branch —
    collapses into the plain failure/idle branches), the `thesis` prop passed to `<PriceChart>`, and the
    `onHintDeclare` prop passed to `<Cockpit>`.
11. `components/Cockpit.tsx` — drop the `HintDock` import/render **and** the now-dead `onHintDeclare`
    prop from the component's own signature plus the `Hint` type import (not just the render call) — a
    real, non-obvious deletion target since it's an orphaned prop nobody calls once `HintDock` is gone.
    `QuotePanel`/`RecentTradesPanel`/`FeaturesPanel`/`TapeStatePanel`/`ObservationsPanel`/`EventLogPanel`
    stay untouched.
12. `components/PriceChart.tsx` — remove **only** the thesis-geometry overlay construction: the `thesis`
    prop and the memoized `thesisSpecs`/price-lines blocks built from `thesis?.geometry`. Tape-state
    markers (`stateSpecs`) keep flowing through the same `extraMarkers`/`extraPriceLines` seam into
    `StructureChart`. This is this file's **only** sanctioned edit this era (T-8, veto-class) — no other
    line in this file changes, and **`StructureChart.tsx` is never touched at all**, not even once.
13. `rm -rf apps/frontend/.next`, rebuild, restart both backend and frontend processes (T-9) — required
    before any browser verification step below; a stale build produces false results in both directions.

**Browser verification (this iteration's primary evidence — screenshot each)**
14. `/journal`, `/studies`, `/performance` each render the app's existing 404.
15. Every kept page's top nav shows exactly two links: "Cockpit" and "Structure".
16. Sim cockpit end to end: Watch `SIM-BUYER` → tape reaches `buyer_control` → Stop, with no thesis
    strip, hint dock, or sound-toggle control rendered anywhere.
17. Cockpit `PriceChart`: candles render, timeframe selector switches timeframes, S/R band overlay
    renders, live tape bars move.
18. `/structure`: Load for the pinned AAPL as-of date renders `StructureChart` with the same 300–302.4
    wall band as before this iteration; confirm `git diff <pre-iteration>..HEAD -- apps/frontend/components/StructureChart.tsx` is empty.
19. The provenance/feed-basis badge still renders its feed label (from the J-01-slimmed
    `GET /research/taxonomy`) on a live/sim watch.
20. Capture a WS frame (`websocat ws://localhost:<port>/tape/SIM-BUYER/stream` or a browser devtools WS
    inspector dump) while `SIM-BUYER` is watched — confirm no `thesis`/`hint` key, all other keys present.

**Close-out**
21. Re-capture the I-9 byte-comparison against `runs/goal-session-clean_slate/iter-1/kept-route-after.txt`
    — expect zero deltas except the documented `meta.ui-routes` 6→2 shrink.
22. `grep -rln` the full orphan-identifier list (TC-11: the 14 api.ts functions, 11 components,
    `onHintDeclare`/`handleHintDeclare`/`hintPrefill`/`survivingThesis`/`ThesisPrefill`) across
    `apps/frontend/` excluding `docs/goal-archive`/`runs/goal-session*` — zero hits; `fetchTaxonomy`
    still hits in both `lib/api.ts` and `FeedBasisBadge.tsx`.
23. Dev handoff at `docs/handoffs/goal-clean_slate-iter-2-dev.md`.

## Out of Scope (carried from the phase spec — do not relitigate)

- MCP tool removal (J-03): `_TOOL_PATHS`/`types.Tool` deletions for `journal`/`analytics`/`studies`,
  `test_mcp_server.py`'s 15-tool contract. Do not touch `test_mcp_server.py` — its one pre-authorized
  failure (`test_static_live_tools_json_byte_identical_to_rest`) stays red; that's J-03's to close.
- `Config` field deletion + the `config_fingerprint` epoch bump (J-04), including any of the 13 pinned
  assertion sites — zero diff on `config.py` or any pin is a hard requirement this iteration, not J-04's.
- J-05's full sentinel close (Case Studies drill-in, full-suite-under-new-pin, cumulative
  diff-vs-inventory) — only its browser-walkable touched-surface subset (sim cockpit + both charts +
  provenance badge + `/structure` Load) is exercised this iteration, per step 3 above.
- Restoring `/structure`'s suppressed `SHOW_CASE_STUDIES` flag — pre-existing, unrelated; still pending
  for whoever plans J-05.
- Hand-editing `NavBar.tsx`, `TopBar.tsx`, or `test_copy_discipline.py` — none need a change (dynamic
  route fetch / no route list / dynamic glob respectively); confirmed during this planning pass.
- Any research-value computation module (`levels.py`, `tradability.py`, `setups.py`, `edge_report*.py`,
  `backtests.py`, `datasets.py`, `bars.py`, `strategies.py`, `profiles.py`, `pnl_ledger.py`) — untouched;
  only the WS transport layer, the nav route list, and frontend presentation code change this iteration.
- Schema migrations, `journal.db` table drops — untouched (not this journey's concern).

## Agents Required

- backend-data: yes -- WS merge removal + `ResearchRegistry` stub deletion in the same commit
  (`app/main.py`, `app/research/routes.py`), `app/meta.py` route-list trim, `test_meta_routes.py` update.
- frontend-ux: yes -- delete 3 pages + 11 components + 14 `lib/api.ts` functions; slim `lib/types.ts`;
  strip the cockpit page's thesis/hint integration; drop `Cockpit.tsx`'s `HintDock`/`onHintDeclare`;
  remove `PriceChart.tsx`'s thesis-geometry overlay only; clean `.next` rebuild.

(This project's agent roster has one implementation agent, `developer`, covering both areas above — see
`.claude/agents/`. There are no separate backend-data/frontend-ux agents to dispatch; one `developer` run
implements the full list in "What to Build" end to end, backend steps first, then frontend, then rebuild,
then browser verification.)

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/main.py` -- delete WS `thesis`/`hint` frame merge + both projection helpers
- `apps/backend/app/research/routes.py` -- delete 4 dead `ResearchRegistry` stubs + `_monitors`; update class docstring
- `apps/backend/app/meta.py` -- trim `UI_ROUTES` to 2 rows (Cockpit, Structure)
- `apps/backend/tests/test_meta_routes.py` -- update 2 tests to 2-route contract, delete 2 tests, leave 2 unchanged
- `apps/frontend/app/journal/`, `apps/frontend/app/studies/`, `apps/frontend/app/performance/` -- delete (pages)
- `apps/frontend/components/{JournalTable,JournalDetailView,JournalFilterBar,ThesisStrip,HintDock,HintLog,SoundCue,StudyList,StudyCreateForm,StudyResultsView,AnalyticsView}.tsx` -- delete (11 files)
- `apps/frontend/lib/api.ts` -- delete 14 functions; keep `fetchTaxonomy`
- `apps/frontend/lib/types.ts` -- delete thesis/hint/journal/study/analytics type families; slim `ResearchTaxonomy`; drop `thesis?`/`hint?` from `TapeSnapshot`
- `apps/frontend/lib/useTapeStream.ts` -- verify via `tsc`; likely no direct edit needed
- `apps/frontend/app/page.tsx` -- remove thesis/hint imports, state, handlers, JSX, and props passed down
- `apps/frontend/components/Cockpit.tsx` -- drop `HintDock` import/render + `onHintDeclare` prop + `Hint` type import
- `apps/frontend/components/PriceChart.tsx` -- remove ONLY the `thesis` prop + `thesisSpecs`/price-lines block
- `apps/frontend/.next/` -- `rm -rf`, rebuild (T-9)
- `docs/handoffs/goal-clean_slate-iter-2-dev.md` -- new, required
- `runs/goal-session-clean_slate/iter-2/` -- new byte-comparison re-capture + WS-frame-capture evidence artifacts
- **Zero diff expected:** `apps/frontend/components/StructureChart.tsx` (veto-class if touched),
  `apps/backend/app/config.py`, all 13 fingerprint pin assertion lines, `apps/backend/app/mcp/__init__.py`,
  `apps/backend/tests/test_mcp_server.py`, `apps/backend/tests/test_copy_discipline.py`,
  `apps/frontend/components/NavBar.tsx`, `apps/frontend/components/TopBar.tsx`, every research-value
  computation module listed under Out of Scope.

## UI Evolution

This iteration is **subtractive only** — no new capability, information, or action is added; the UI
Evolution policy still applies because user-visible surface area changes materially.

- New user-facing capability: **None.** Capability is removed: the manual thesis-declare/resolve/action/
  review workflow, the hint-dock declare affordance, the sound cue, and the studies/performance
  workbenches are all deleted.
- New information displayed: **None — less is displayed.** The thesis strip, hint dock,
  verdict/stance/grade/excursion data, and the studies/performance pages' content no longer render
  anywhere.
- New user actions: **None.** Thesis-declare/resolve/review, hint-declare, and study create/cancel are
  all removed; no replacement action is added.
- UI surface changes: `/journal`, `/journal/[id]`, `/studies`, `/performance` no longer exist (the app's
  real 404, not a redirect or placeholder). Top nav shrinks from 5 links to exactly 2 (Cockpit,
  Structure). The cockpit page loses the thesis strip, hint dock, and sound-cue toggle; its panel grid
  (quote/trades/features/observations/event-log/tape-state) and both charts are otherwise unchanged.
- Navigation changes: nav row count drops from 5 to 2 (data-driven from `app/meta.py` ROUTES via
  `GET /meta/ui-routes` — no nav component is hand-edited). No new nav entries.

## Visual Requirements

- Component patterns: none new. No component is added or restyled; work is deletion plus one prop
  removal on an existing chart container (`PriceChart.tsx`). Reuse the app's existing not-found treatment
  for the three deleted routes — do not build a custom 404/tombstone page (goal.md explicitly forbids
  "coming soon" placeholders).
- Layout: unchanged — persistent top nav + main content area; the nav bar's own layout doesn't change
  shape when it renders 2 links instead of 5 (`NavBar.tsx` needs no edit).
- Key visual effects: none new. Preserve the existing dark-only, dense, terminal-grade styling on every
  surviving surface; no glassmorphism/glow/gradient work is in scope this iteration.
- States to handle: the 404 state for the 3 deleted routes is the app's pre-existing not-found render —
  verify it looks deliberate (styled, not a blank screen or raw error), not that it's newly built. The
  "no thesis strip / no hint dock" cockpit state needs no empty-state design — those slots are removed
  entirely, not replaced with a placeholder.

## Key Test Scenarios

(Full TC-1..TC-18 wording in the phase spec; condensed here — see spec for exact JSON/grep commands.)

- `python -c "import app.main"` succeeds with no `NameError`/`AttributeError`/`ImportError` after the WS
  merge + registry stub deletions (TC-1).
- `GET /meta/ui-routes` returns exactly the 2-row Cockpit+Structure payload (TC-2).
- Three 404 screenshots (`/journal`, `/studies`, `/performance`) + one 2-link-nav screenshot (TC-3, TC-4).
- Sim cockpit flow (`SIM-BUYER` → `buyer_control` → Stop) screenshot shows no thesis strip / hint dock /
  sound toggle anywhere (TC-5).
- Cockpit `PriceChart` screenshot: candles + timeframe switch + band overlay + live tape bars all work
  (TC-6); `/structure` AAPL Load screenshot shows the same 300–302.4 wall band, and
  `git diff <pre-iteration>..HEAD -- apps/frontend/components/StructureChart.tsx` is empty (TC-7).
- Provenance badge still renders its feed label from `GET /research/taxonomy` on a live/sim watch (TC-8).
- Captured WS frame has no `thesis`/`hint` key, all other pre-existing keys present (TC-9).
- `tsc --noEmit` (or `npm run build`) in `apps/frontend` completes with zero type errors (TC-10).
- The full orphan-identifier grep (14 api.ts fns + 11 components + 5 dead page.tsx/Cockpit identifiers)
  returns zero hits outside history dirs; `fetchTaxonomy` still hits in both its owner and caller (TC-11).
- `pytest apps/backend/tests/test_meta_routes.py` — 0 failed (TC-12).
- `pytest apps/backend/tests/test_copy_discipline.py` — 0 failed, unedited (TC-13).
- I-9 byte-comparison re-capture vs iter-1's `kept-route-after.txt` — identical except `meta.ui-routes`
  (TC-14).
- Zero diff on the 13 fingerprint pin sites + `config.py`; `config_fingerprint()` still prints
  `4d665603569b9dbf` (TC-15).
- Zero lines touched under `docs/goal-archive/`, `runs/goal-session-*`,
  `reports/goal-session-*-delivered.md`, or journal.db's existing rows (TC-16).
- Full backend suite: same single pre-authorized failure as iter-1
  (`test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest`), 0 other failures/errors,
  collected-test count unchanged from iter-1's post-J-01 run (TC-17).
- `test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`, `test_price_chart_confluence.py`
  diff empty and all pass (TC-18).
