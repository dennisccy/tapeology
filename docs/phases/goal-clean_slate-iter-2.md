# Goal Iteration 2 — Frontend + WS demolition, the two-page product (J-02)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** clean_slate
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-02
- **Required-still-passing journeys:** J-01, J-05
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

Delete the frontend pages/components/types/api-functions for the manual journal/studies/performance surfaces, strip the cockpit's thesis/hint/sound integration and the WS `thesis`/`hint` frame merge, and trim the nav to exactly Cockpit + Structure — so a real user, in a browser, sees exactly the two-page kept product, with both charts and the provenance badge working exactly as shipped, and the three deleted routes honestly 404.

## BACKGROUND

Iteration 1 (full depth) landed J-01: 11 backend modules deleted, 2 relocations proven byte-identical, 14 routes 404, taxonomy slimmed, `config_fingerprint` unchanged — independently re-verified by the evaluator, coherence PASS. Its Next-Step Recommendation explicitly targets **J-02 at full depth**, the natural next step in goal.md's own J-01→J-02→J-03→J-04→J-05 dependency order (rubric rule 3: J-02 can only safely stop the frontend calling the 14 now-404 routes because they are already gone). Depth **full** is independently justified here too: this iteration crosses the backend+frontend boundary (WS merge removal + `ResearchRegistry` stub cleanup in `main.py`/`routes.py`, `app/meta.py` ROUTES trim), is browser-verifiable (404 pages, nav, sim cockpit flow, both charts, a captured WS frame), and is large/structural (3 pages, 11 components, 14 `api.ts` functions, a `types.ts` family, the cockpit page's state/handlers, `PriceChart.tsx`'s overlay build) — three independent triggers from the Picking-depth rubric. Per rule 5 (never bundle two risky journeys), J-02 runs alone this iteration; J-03 (MCP) stays untouched. Last coherence verdict was PASS (not FAIL), so this is normal next-scope work, not a consolidation pass.

Three items carried forward from iter-1's eval Next-Step Recommendation, all independently re-verified live against the current commit (not the stale `fa76460` anchors) during this iteration's planning:
1. **Delete the four now-genuinely-dead `ResearchRegistry` stubs** (`monitor_for`, `projection_for`, `_surviving_projection`, `hint_projection_for`) plus the `_monitors` dict, in the SAME commit as the WS merge removal — current anchors re-verified at `apps/backend/app/research/routes.py:219-305` (class docstring, `__init__`, and each method's own docstring explicitly say they exist ONLY because `main.py`'s WS merge still calls them).
2. **Do not touch `test_mcp_server.py`** — its one red case (`test_static_live_tools_json_byte_identical_to_rest`, proxying `journal`→now-404) is J-03's to close.
3. **`SHOW_CASE_STUDIES = false`** (`apps/frontend/app/structure/page.tsx:335`) is still unresolved — re-verified still `false` this iteration. J-02's own acceptance text never mentions Case Studies, so it is out of scope here too; carried forward again for whoever plans J-05.

Two new findings from this iteration's own planning (not previously surfaced): (a) `apps/backend/tests/test_copy_discipline.py`'s frontend-literal walk (`_FRONTEND_ROOT.glob("components/**/*.tsx")` + `app/**/*.tsx` + `app/**/*.ts`) is a **dynamic glob**, not a hardcoded file list — it needs **no manual edit**; deleting the pages/components automatically shrinks what it scans, closing the "shrinks in J-02" note from iter-1's spec. (b) `NavBar.tsx` already fetches `GET /meta/ui-routes` at runtime with, per its own source comment, "deliberately NO hardcoded route list here, not even as a fallback" — the nav trim is a **backend-only** edit (`app/meta.py`); `TopBar.tsx` (the cockpit's separate local status bar: symbol search, data-source selector, feed-basis badge) carries no route list at all. Neither file needs touching for the nav to shrink. A third completeness catch, beyond goal.md's own I-7 wording: `Cockpit.tsx`'s `onHintDeclare` prop (and its `Hint` type import) exists ONLY to wire `<HintDock onDeclare={...}>` — once `HintDock` is removed, `onHintDeclare` becomes a dead, never-invoked prop on `Cockpit` and must be deleted from its signature too (and the caller in `app/page.tsx`), not just from the render body, or it is exactly the "orphaned" surface the anti-goals forbid.

A logged interpretation call (see `runs/goal-session-clean_slate/state/assumptions.md`): the I-9 byte-comparison protocol's step-2 wording ("`/research/taxonomy` is the ONE sanctioned diff") is read as *cumulative per-journey*, not a single fixed exception — this iteration's own re-capture is expected to show exactly one NEW sanctioned diff (`GET /meta/ui-routes`, 6→2 rows), on top of J-01's already-accepted taxonomy diff, because J-02's own acceptance text explicitly requires `GET /meta/ui-routes` to list only the kept routes.

## IN SCOPE

### Backend
- [ ] Remove the WS `thesis`/`hint` merge from `app/main.py`'s `/tape/{ticker}/stream` handler: delete `frame["thesis"] = _thesis_projection(ticker)` and `frame["hint"] = _hint_projection(ticker)` (current anchors: lines 595, 600) and both helper functions `_thesis_projection`/`_hint_projection` (607-628) — the frame becomes the engine projection only (I-5 WS half).
- [ ] In the SAME commit, delete `ResearchRegistry`'s now-dead stub surface in `app/research/routes.py` (current anchors 219-305): the `_monitors` dict (`__init__` line 237) and the methods `monitor_for` (266), `projection_for` (269), `_surviving_projection` (283), `hint_projection_for` (294) — their only caller was the WS merge just removed above; update the class docstring accordingly (it currently explains why they were "kept ... ONLY because" the WS merge called them).
- [ ] Delete the four journal-era rows from `app/meta.py`'s `UI_ROUTES` tuple (`/journal`, `/journal/[id]`, `/studies`, `/performance`) — leaves exactly the Cockpit (`/`) and Structure (`/structure`) rows. Do not hand-edit `NavBar.tsx` — it already renders `GET /meta/ui-routes` verbatim with no hardcoded fallback list; the nav shrinks automatically.
- [ ] Update `apps/backend/tests/test_meta_routes.py` to the 2-route contract: `test_ui_routes_lists_exactly_the_live_routes` and `test_ui_routes_top_bar_entries_match_the_rendered_nav_set` assert the 2-row payload; `test_ui_routes_includes_performance_now_its_page_ships` and `test_ui_routes_represents_journal_detail_honestly` are deleted (they assert routes that no longer exist); `test_ui_routes_every_entry_carries_path_and_label` and `test_ui_routes_includes_structure_now_its_page_ships` are unchanged.

### Frontend
- [ ] Delete pages `apps/frontend/app/journal/` (incl. `[id]/`), `apps/frontend/app/studies/`, `apps/frontend/app/performance/`.
- [ ] Delete the eleven journal-era components: `JournalTable.tsx`, `JournalDetailView.tsx`, `JournalFilterBar.tsx`, `ThesisStrip.tsx`, `HintDock.tsx`, `HintLog.tsx`, `SoundCue.tsx`, `StudyList.tsx`, `StudyCreateForm.tsx`, `StudyResultsView.tsx`, `AnalyticsView.tsx`.
- [ ] Delete the 14 named `lib/api.ts` functions (I-7): `declareThesis`, `resolveThesis`, `recordAction`, `saveReview`, `fetchActiveThesis`, `fetchActiveHint`, `fetchHints`, `fetchJournal`, `fetchJournalDetail`, `fetchAnalytics`, `createStudy`, `fetchStudies`, `fetchStudy`, `cancelStudy`. `fetchTaxonomy` is KEPT (`FeedBasisBadge.tsx`'s only caller).
- [ ] `lib/types.ts`: delete the thesis/hint/journal/study/analytics families (`ThesisVerdict`, `ThesisStatement`, `ThesisMarks`, `ThesisGeometry`, the stance/cue types, `ThesisProjection`, `Hint`, `HintsTaxonomy`, `ThesisGrades`, `ThesisExcursions`, `JournalDetailThesis`, and the other journal/analytics/study result types); slim `ResearchTaxonomy` to the kept shape (feed_basis + source labels); drop the `thesis`/`hint` fields from `TapeSnapshot` (current anchors ~766-773).
- [ ] `app/page.tsx` (cockpit): remove the thesis/hint integration — the `fetchActiveThesis` import and `Hint`/`ThesisProjection`/`ThesisStrip`/`ThesisPrefill` imports, the `survivingThesis` state and its post-Stop `GET /research/thesis/active` read in `handleStop`, `hintPrefill`/`handleHintDeclare`, the `<ThesisStrip>` renders (both the live one between chart and grid, and the post-stop "surviving thesis" branch — collapses into the plain `failure`/idle branches), the `thesis` prop passed to `<PriceChart>`, and the `onHintDeclare` prop passed to `<Cockpit>`.
- [ ] `Cockpit.tsx`: drop the `HintDock` import/render AND the now-dead `onHintDeclare` prop from its own signature + the `Hint` type import (not just the render call) — `QuotePanel`/`RecentTradesPanel`/`FeaturesPanel`/`TapeStatePanel`/`ObservationsPanel`/`EventLogPanel` stay untouched.
- [ ] `PriceChart.tsx`: remove ONLY the thesis-geometry overlay construction — the `thesis`/`ThesisProjection` prop and the memoized `thesisSpecs`/price-lines blocks built from `thesis?.geometry` — tape-state markers (`stateSpecs`) keep flowing through the same `extraMarkers`/`extraPriceLines` seam into `StructureChart`. No other edit to this file (T-8 veto-class).
- [ ] `rm -rf apps/frontend/.next`, rebuild, and restart both the backend and frontend processes (T-9) before any browser verification step below.

### Browser verification (this iteration's primary evidence — J-02 is browser-verifiable)
- [ ] `/journal`, `/studies`, `/performance` each render the app's existing 404 (screenshot each).
- [ ] Every kept page's top nav shows exactly two links, "Cockpit" and "Structure" (screenshot).
- [ ] Sim cockpit flow end to end: Watch `SIM-BUYER` → tape reaches `buyer_control` → Stop, with no thesis strip, hint dock, or sound-toggle control rendered anywhere (screenshot).
- [ ] Cockpit `PriceChart`: candles render, the timeframe selector switches timeframes, the S/R band overlay renders, live tape bars move (screenshot).
- [ ] `/structure`: Load for the pinned AAPL as-of date still renders the `StructureChart` (candles + the 300–302.4-class wall band) exactly as before this iteration (screenshot).
- [ ] The provenance/feed-basis badge still renders its feed label (from the J-01-slimmed `GET /research/taxonomy`) on a live/sim watch (screenshot).
- [ ] A captured WS frame (e.g. `websocat ws://localhost:<port>/tape/SIM-BUYER/stream` or a browser devtools network/WS inspector dump) contains no `thesis` key and no `hint` key.

### New user-facing capability
None — this iteration REMOVES capability. The manual thesis-declare/resolve/action/review workflow, the hint-dock declare affordance, the sound cue, and the studies/performance workbenches are all deleted; nothing new is added.

### New information displayed
None — if anything, LESS is displayed: the thesis strip, hint dock, verdict/stance/grade/excursion data, and the studies/performance pages' content no longer render anywhere.

### New user actions
None — the thesis-declare/resolve/review actions, the hint-declare affordance, and study create/cancel actions are all removed. No replacement action is added.

### UI surface changes
`/journal`, `/journal/[id]`, `/studies`, `/performance` no longer exist (404, not redirects, not placeholders). The top nav shrinks from 5 links to exactly 2 (Cockpit, Structure). The cockpit page loses the thesis strip, hint dock, and sound-cue toggle; its panel grid (quote/trades/features/observations/event-log/tape-state) and both charts are otherwise unchanged.

### Product surface delta
The product becomes exactly the two-page instrument goal.md's Vision names: Cockpit + Structure, nothing else — a subtractive delta, not an addition. Every kept behavior (both charts, the provenance badge, levels/zones, tradable map, edge report, strategy registry) works exactly as shipped before this iteration.

### Blueprint conformance
`/` (Cockpit) and `/structure` (Structure) — both already-registered homes in `blueprint.md`'s Information Architecture. This iteration REALIZES the blueprint's already-documented target nav skeleton (the 2-item nav) and its "Removed this interlude" list verbatim; `blueprint.md` was re-read during planning and already anticipates this exact end state (including the Data Contract's "Route / nav inventory" row, which already reads "after J-02: exactly Cockpit + Structure") — **no blueprint edit is required this iteration.**

### Data-contract additions
None. No new displayed value is introduced; this iteration only deletes values already listed in `blueprint.md`'s "Removed entirely this interlude, with their owners" list (active thesis, hints, etc. — no replacement, no new home). The one already-registered Data Contract row whose SERVED payload legitimately changes is "Route / nav inventory" (`GET /meta/ui-routes`, owner `app/meta.py` ROUTES) — its shrink from 6 to 2 rows is this iteration's own documented, sanctioned change, already anticipated in `blueprint.md`'s Notes column.

## OUT OF SCOPE

- MCP tool removal (J-03) — `_TOOL_PATHS`/`types.Tool` deletions for `journal`/`analytics`/`studies`, and `test_mcp_server.py`'s 15-tool contract update — deferred to iteration 3. The three MCP tools keep proxying to now-404 routes via the existing honest-404 `get_endpoint` contract this iteration; `test_mcp_server.py`'s one red case stays red (J-03's to close) — do not touch that file.
- Config field deletion + the `config_fingerprint` epoch bump (J-04), including any of the 13 pinned assertion sites — strictly deferred to iteration 4 (T-3 pin discipline).
- J-05's full sentinel close (Case Studies drill-in, full-suite-green-under-the-new-pin, cumulative diff-vs-inventory cross-check) — this iteration re-verifies J-05's browser-walkable KEPT-surface subset that this iteration's own changes touch (sim cockpit + both charts + provenance badge + `/structure` Load) as part of J-02's own acceptance, but does not close J-05 itself (it depends on J-04).
- Restoring `SHOW_CASE_STUDIES` on `/structure` — pre-existing, unrelated flag; not touched here (not part of J-02's acceptance); still pending for whoever plans J-05 (restore vs. operator rescopes the acceptance line).
- Hand-editing `NavBar.tsx` or `TopBar.tsx` — neither needs a change; `NavBar.tsx` already reads `GET /meta/ui-routes` dynamically with no hardcoded fallback list (verified during planning), and `TopBar.tsx` carries no route list at all.
- Hand-editing `test_copy_discipline.py` — its frontend-literal walk is a dynamic glob over `components/**` + `app/**`; it needs no manual edit and shrinks automatically once the files above are deleted.
- Any edit to `StructureChart.tsx` — stays byte-unmodified this era (T-8 veto-class); this iteration's only chart-adjacent edit is `PriceChart.tsx`'s thesis-geometry overlay removal.
- Schema migrations, `journal.db` table drops, or any edit to `_migrate`/`_create_schema` — untouched (T-4; not this journey's concern anyway).
- Any research-value computation module (`levels.py`, `tradability.py`, `setups.py`, `edge_report*.py`, `backtests.py`, `datasets.py`, `bars.py`, `strategies.py`, `profiles.py`, `pnl_ledger.py`) — none of these are touched this iteration; only the WS transport layer, the nav route list, and frontend presentation code change.

## DEFINITION OF DONE

- [ ] J-02 passes: nav shows exactly Cockpit + Structure on every kept page; `/journal`, `/journal/[id]`, `/studies`, `/performance` each render the app's 404 (browser-verified, screenshots); the sim cockpit flow (`SIM-BUYER` → `buyer_control`) settles `buyer_control` end to end with no thesis strip, hint dock, or sound toggle anywhere; both charts render their full pre-iteration behavior (cockpit `PriceChart`: candles + timeframe switch + band overlay + live tape bars; `/structure`'s `StructureChart` + Load flow unchanged); the provenance badge still renders from the slimmed taxonomy; a captured WS frame contains no `thesis`/`hint` key; `GET /meta/ui-routes` lists only the 2 kept routes
- [ ] `StructureChart.tsx`'s diff against the pre-iteration snapshot is exactly empty (T-8 veto-class)
- [ ] `PriceChart.tsx`'s only edit is the thesis-geometry overlay removal; the three chart guard suites (`test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`, `test_price_chart_confluence.py`) pass byte-unmodified
- [ ] J-01 (Required-still-passing) still holds: the I-9 byte-comparison re-capture against `runs/goal-session-clean_slate/iter-1/kept-route-after.txt` shows zero deltas except the documented `meta.ui-routes` shrink
- [ ] `test_meta_routes.py` updated to the 2-route contract and passes; no other backend test file is added or removed this iteration
- [ ] Full backend suite passes with the SAME single pre-authorized failure as iter-1 (`test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest`, J-03's to close) and zero OTHER failures/errors
- [ ] No anti-goal violation introduced (rails 1, 3, 5, 6, 8, 9, plus the interlude-specific "deletion complete never cosmetic," "never modify the charts beyond the one named edit," "never touch a historical record," "no guard weakening")
- [ ] `rm -rf apps/frontend/.next` clean rebuild performed before browser verification (T-9)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-clean_slate-iter-2-dev.md`

## TESTING REQUIREMENTS

- Browser: J-02 in full (404s on the 3 deleted pages, the 2-item nav, the sim cockpit flow, both charts, the provenance badge, a captured WS frame) — see TC-3 through TC-9 below. J-05's browser-walkable subset touched by this iteration's changes is exercised as part of the same browser pass (TC-5 through TC-8).
- Unit/integration: full `apps/backend` pytest suite; `test_meta_routes.py`'s updated 2-route contract; `test_copy_discipline.py` unedited but re-run (dynamic glob); the I-9 byte-comparison capture-and-diff.
- Error cases: each of the 3 deleted pages must render the app's real not-found treatment (not a blank screen, not a redirect, not a 500); the WS stream must keep functioning normally (no `thesis`/`hint` keys, but every other key present) even when the research registry has nothing to project — never a WS error/close on account of this change.

Test-first contract:

- TC-1: given the WS `thesis`/`hint` merge and the four dead `ResearchRegistry` methods + `_monitors` are deleted, when `python -c "import app.main"` runs, then it imports with no `NameError`/`AttributeError`/`ImportError`.
- TC-2: given `app/meta.py`'s `UI_ROUTES` tuple is trimmed to the 2 kept rows, when `GET /meta/ui-routes` is curled, then the JSON response is exactly `{"routes": [{"path": "/", "label": "Cockpit", "nav": true}, {"path": "/structure", "label": "Structure", "nav": true}]}`.
- TC-3: given the three pages are deleted, when a browser navigates to `/journal`, `/studies`, and `/performance`, then each renders the app's existing not-found 404 page (screenshot each).
- TC-4: given the trimmed nav, when a browser loads any kept page, then the top nav bar shows exactly two links labeled "Cockpit" and "Structure" (screenshot).
- TC-5: given the cockpit's thesis/hint/sound integration is removed, when a browser watches `SIM-BUYER` end to end (Watch → tape reaches `buyer_control` → Stop), then the cockpit settles `buyer_control` with no thesis strip, hint dock, or sound-toggle control rendered anywhere on the page (screenshot).
- TC-6: given `PriceChart.tsx`'s thesis-geometry overlay build is removed but the component is otherwise unchanged, when a browser watches a ticker on the cockpit, then the chart renders candles, the timeframe selector switches timeframes, the S/R band overlay renders, and live tape bars move (screenshot).
- TC-7: given `StructureChart.tsx` is byte-unmodified this iteration, when a browser loads `/structure` and clicks Load for the pinned AAPL as-of date, then the chart renders the same 300–302.4-class wall band as before this iteration (screenshot) and `git diff <pre-iteration-snapshot>..HEAD -- apps/frontend/components/StructureChart.tsx` is empty.
- TC-8: given the J-01-slimmed taxonomy is unaffected by this iteration, when a browser watches a live/sim ticker, then the provenance/feed-basis badge still renders its feed label sourced from `GET /research/taxonomy`.
- TC-9: given the WS frame no longer merges `thesis`/`hint`, when a WS frame is captured (e.g. via `websocat` or a browser devtools WS inspector dump) while `SIM-BUYER` is watched, then the captured JSON contains no `thesis` key and no `hint` key, while every other pre-existing key (`ticker`, `stream_status`, `tape_state`, `features`, `recent_trades`, etc.) is still present.
- TC-10: given `lib/types.ts` drops the thesis/hint families and slims `ResearchTaxonomy`, when the frontend TypeScript build runs (`tsc --noEmit` or `npm run build` in `apps/frontend`), then it completes with zero type errors.
- TC-11: given the 14 named `lib/api.ts` functions, the eleven components, and the dead `Cockpit`/`page.tsx` identifiers (`onHintDeclare`, `handleHintDeclare`, `hintPrefill`, `survivingThesis`, `ThesisPrefill`) are all deleted, when `grep -rln "declareThesis|resolveThesis|recordAction|saveReview|fetchActiveThesis|fetchActiveHint|fetchHints|fetchJournal|fetchJournalDetail|fetchAnalytics|createStudy|fetchStudies|fetchStudy|cancelStudy|JournalTable|JournalDetailView|JournalFilterBar|ThesisStrip|HintDock|HintLog|SoundCue|StudyList|StudyCreateForm|StudyResultsView|AnalyticsView|onHintDeclare|handleHintDeclare|hintPrefill|survivingThesis|ThesisPrefill" apps/frontend/ | grep -Ev "docs/goal-archive|runs/goal-session"` is run, then it returns zero hits, AND `grep -n "fetchTaxonomy" apps/frontend/lib/api.ts apps/frontend/components/FeedBasisBadge.tsx` returns a hit in both files (the kept caller survives).
- TC-12: given `test_meta_routes.py` is updated to the 2-route contract, when `pytest apps/backend/tests/test_meta_routes.py` runs, then it reports 0 failed.
- TC-13: given no manual edit is made to `test_copy_discipline.py`, when `pytest apps/backend/tests/test_copy_discipline.py` runs after the frontend deletions, then it reports 0 failed (fewer files scanned by the same dynamic glob, same lint rules).
- TC-14: given the I-9 byte-comparison re-capture is run against `runs/goal-session-clean_slate/iter-1/kept-route-after.txt`, when every KEPT `/research`+`/tape`+`/meta` GET route is curled and sha256-compared, then every hash is identical to its iter-1 entry EXCEPT `meta.ui-routes` (this iteration's own sanctioned, documented shrink).
- TC-15: given the full iteration diff, when the 13 fingerprint pin assertion sites (I-9) and `apps/backend/app/config.py` are diffed against the pre-iteration snapshot, then none of those 14 items differ (T-3), and `python -c "from app.config import Config; print(Config().config_fingerprint())"` still prints `4d665603569b9dbf`.
- TC-16: given the full iteration diff, when checked against the "never touch a historical record" anti-goal, then zero lines under `docs/goal-archive/`, `runs/goal-session-*`, `reports/goal-session-*-delivered.md`, or `journal.db`'s existing rows are touched.
- TC-17: given the full backend suite runs after this iteration's deletions/edits, when `pytest apps/backend/tests/` runs, then it reports exactly the same single pre-authorized failure as iter-1 (`test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest`) and 0 other failures/errors, with a collected-test count unchanged from iter-1's post-J-01 run (no backend test file is added or removed this iteration — only `test_meta_routes.py`'s existing assertions are edited).
- TC-18: given `test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`, and `test_price_chart_confluence.py` are not edited this iteration, when each is diffed against the pre-iteration snapshot, then each diff is exactly empty, and when `pytest` runs each file, then each reports 0 failed.

## NOTES

- **Assumption logged.** `runs/goal-session-clean_slate/state/assumptions.md` now has an `iter-2 — goal-decomposer` entry explaining the cumulative reading of the I-9 "taxonomy is the ONE sanctioned diff" wording (see BACKGROUND) — read it before scoring TC-14 so the expected `meta.ui-routes` diff is not mistaken for a violation.
- **`Cockpit.tsx`'s `onHintDeclare` prop is a real, non-obvious deletion target** goal.md's own I-7 wording only names `HintDock`'s import/render; the `onHintDeclare` prop + `Hint` type import on `Cockpit`'s own signature exist solely to wire it and must go too, or it's an orphaned prop nobody calls.
- **`structure/page.tsx:1305`** contains the substring "StudyResultsView" — verified during planning to be prose inside a code COMMENT (explaining why `/structure`'s own cancel-copy is intentionally NOT reused from that component), not an import. Not a T-12 blocker; noted so the grep-before-delete step isn't second-guessed over a false positive.
- **`SHOW_CASE_STUDIES = false`** (carried forward a second time, still unresolved, still out of scope here): must be resolved — restore the flag vs. the operator rescopes J-05's literal "Case Study drill-in" acceptance clause — before J-05 can close. Surface again when J-05 is planned.
- **Required-still-passing scoping.** J-01 has no browser component (its own acceptance is keyless/automated) — its regression check this iteration is the I-9 byte-comparison re-capture (TC-14) plus the full suite (TC-17), not a browser replay. J-05 is included per the session's established precedent (it is goal.md's continuously-guarding sentinel, not yet `passing`) — its regression check this iteration is the browser walk in TC-5 through TC-8, covering exactly the kept surfaces this iteration's own diff touches (both charts, provenance badge, sim cockpit); J-05's OTHER acceptance clauses (Case Studies, full-suite-under-new-pin, cumulative diff-vs-inventory) are out of scope until J-04/J-05's own iteration. Neither J-01 nor J-05 yet has a stored golden replay script this early in the session — both are covered by direct re-verification this iteration rather than deterministic replay; a wider golden-refreshing regression pass is expected once more journeys are `passing`.
