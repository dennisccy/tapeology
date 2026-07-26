# goal-desk-iter-4 Execution Plan

Era B "The Desk", target journey **J-04** (the `/desk` briefing page) at **full depth** (first
frontend iteration of the era — new `UI_ROUTES` nav-skeleton row 2→3, a blueprint IA change the
coherence gate must re-audit; audit + ux-regression + closure + browser QA all apply). Follows
iter-3 `eval.md`'s Next-Step Recommendation verbatim. Required-still-passing: J-01, J-02, J-03,
J-07 — do not re-verify their internals (`journey-history.json` carries the evidence); just keep a
zero-diff on the frozen owners named below. No scope creep found: every IN SCOPE item traces to a
Must-have journey step or a named audit/eval follow-up (B2/B4/B9/B10, T3), and the phase spec's own
OUT OF SCOPE section is honored below — do not build J-05 (history click-through, `/structure`
prefill/drill-in), J-06 (MCP tools), a date-picker, or touch `/structure`/PriceChart/StructureChart/
Cockpit/`_select_best_band`/`compute_screen`'s row-skip logic/tradability.py/levels.py/bars.py/
bar_index.py/config.py.

## What to Build

Backend (all in `apps/backend/`, zero new `Config` field, pin stays `08e471b10130e1e2`):
- `UI_ROUTES` in `app/meta.py` gains a third entry `{"path": "/desk", "label": "Desk", "nav": True}`
  after Structure — nav and MCP `ui_route_map` follow automatically via `GET /meta/ui-routes`; never
  hand-edit `NavBar.tsx`.
- `DeskScreenComputeManager`'s job snapshot gains `reused: bool` + `screen_id: str | None` (closes
  audit B2) so `/desk` can tell "reused the existing snapshot" from "just computed it" — see Files
  section for the exact threading. Zero change to `compute_screen`'s row/skip computation or
  `ScreenStore`'s persisted snapshot shape.
- `POST /research/desk/screen/compute` refuses (honest 4xx, naming the missing universe, mirroring
  `desk_topup_compute.py:352-356`'s message) when no universe snapshot is registered, instead of
  persisting a permanent empty snapshot (closes audit B4). `ScreenStore.list()` shows zero new
  records before and after.
- `UniverseStore.record` (`desk_universe.py:418`) gains the same corrupt-file `.exists()` guard
  `ScreenStore.record` already has (`desk_screen.py:467-473`) — raise an integrity error instead of
  silently overwriting a damaged file at the same checksum path (closes iter-1 audit B3 / iter-3
  lesson).
- Test hygiene: `test_desk_screen_compute.py`'s `route_ctx` fixture (~405-423) scopes
  `TAPEOLOGY_DATASET_DIR` to `tmp_path` — currently the one `route_ctx` in its siblings that reads
  the ambient `.data/datasets` tree (closes audit T3). Zero production code change.
- Test-infra, before dispatching browser QA / the replay lane (not application code): warm the
  `tradability_cache` for AAPL as-of `2026-06-22T21:00:00Z` (one `/structure` Load, or a direct
  `GET /research/tradability` call) on the SAME backend instance that will serve both browser QA and
  the deterministic replay lane — this is the first iteration J-07's `journey-scripts/J-07.json` step
  8 is actually replayed (browser QA was `SKIPPED` iter-0..3), so its cold-cache false-negative risk
  is live for the first time.
- `journey-scripts/J-07.json` step 8: set its own `"timeout_ms": 20000` explicitly (the replay
  engine's hard-clamped max) instead of inheriting the file's `15000` default. The assertion target
  (a plain `<td data-testid="tradable-band-range">` cell, confirmed never chart/SVG-embedded) is
  unchanged — only the timeout.

Frontend (all in `apps/frontend/`):
- New page `apps/frontend/app/desk/page.tsx` — briefing table, provenance line, honestly-grouped
  skipped section, read-only screen-history list, Run Screen + Top-up buttons with live progress/
  cancel. Full behavior spec is in the phase spec's IN SCOPE > Frontend section (mirrored into UI
  Evolution / Visual Requirements / Key Test Scenarios below) — read
  `docs/phases/goal-desk-iter-4.md` lines 147-189 for the byte-exact bullet list before implementing.
- `apps/frontend/lib/api.ts`: add `fetchDeskScreen`, `triggerDeskScreenCompute`,
  `fetchDeskScreenCompute`, `cancelDeskScreenCompute`, `triggerDeskTopupCompute`,
  `fetchDeskTopupCompute`, `cancelDeskTopupCompute` — mirror `triggerEdgeReportCompute` /
  `fetchEdgeReportCompute` / `cancelEdgeReportCompute` (`lib/api.ts:844/877/894`) exact `{ok, data,
  error}` shape and 422/unreachable-fold behavior byte-for-byte.
- `apps/frontend/lib/types.ts`: add the desk screen snapshot/row/skip TS interfaces and the two
  compute-snapshot interfaces, matching `blueprint.md`'s registered shapes field-for-field (see Files
  section for the exact shapes) — mirror `EdgeReportComputeSnapshot` (`lib/types.ts:752`)'s pattern.

## Agents Required

- developer: yes -- one full-stack dispatch implementing both the Backend and Frontend IN SCOPE
  lists above in the same iteration (this project's `developer` agent handles both; there is no
  separate backend/frontend agent split). Frontend work is entirely new (`Frontend Present: no` on
  J-01/J-02/J-03), so the developer must do the `apps/frontend/.next` clean-rebuild (T-9) before any
  local verification.

## Frontend Present
yes

## Files to Create/Modify

Backend:
- `apps/backend/app/meta.py` -- append the `/desk` `UI_ROUTES` entry (3rd row).
- `apps/backend/tests/test_meta_routes.py` -- widen `test_ui_routes_lists_exactly_the_live_routes`'s
  literal 2-route list and `test_ui_routes_top_bar_entries_match_the_rendered_nav_set`'s `len(routes)
  == 2` + `top_bar == [...]` to the 3-route set (`/`, `/structure`, `/desk`) in nav order; scan the
  file for any other hardcoded `2` route-count literal. (`test_ui_routes_every_entry_carries_path_
  and_label` and `test_ui_routes_includes_structure_now_its_page_ships` need no change; consider a
  parallel `test_ui_routes_includes_desk_now_its_page_ships` for symmetry with the existing Structure
  test, optional.)
- `apps/backend/app/research/desk_screen_compute.py` -- thread `reused`/`screen_id` onto the job
  snapshot: `run_screen_and_record` (currently returns just the record dict, or `None` if cancelled)
  must also communicate whether the returned record was pre-existing (the `ScreenAlreadyRecorded`
  catch path, ~line 107) vs freshly written (the `screen_store.record(...)` success path, ~line 98)
  so `_work` (~line 187, which today discards the return value entirely) and `_resolve` (~line 204,
  currently `(job_id, state, *, error)`) can populate the terminal snapshot's `reused: bool` +
  `screen_id: str | None`. Initial/`running` state: `reused: false`, `screen_id: null`. Cancelled:
  both stay `false`/`null` (nothing was recorded). How the boolean is threaded (tuple return, small
  result type, etc.) is an implementation choice.
- `apps/backend/app/research/desk_routes.py` -- `trigger_desk_screen_compute`: before starting the
  job, check the universe store has at least one snapshot; if not, raise an honest 4xx naming the
  missing universe (mirror `desk_topup_compute.py:352-356`'s wording), persisting nothing.
- `apps/backend/app/research/desk_universe.py` -- `UniverseStore.record` (~line 418, right before
  `self._path(snapshot_id).write_text(...)`): if `self._path(snapshot_id).exists()`, raise an
  integrity error instead of overwriting (mirror `desk_screen.py:467-473`'s guard + message style).
- `apps/backend/tests/test_desk_screen_compute.py` -- `route_ctx` fixture: add
  `monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))`; add tests proving
  `reused`/`screen_id` distinguish a fresh compute from a pure reuse (TC-7/TC-8) and proving the
  no-universe refusal persists zero records (TC-9).
- `apps/backend/tests/test_desk_universe.py` -- new test mirroring
  `test_recording_over_a_corrupted_file_at_the_same_key_is_refused_never_a_silent_overwrite` (already
  in `test_desk_screen.py`) for `UniverseStore.record` (TC-10).
- `journey-scripts/J-07.json` -- step 8 `"timeout_ms": 20000`.
- `docs/handoffs/goal-desk-iter-4-dev.md` -- new, dev handoff.

Frontend:
- `apps/frontend/app/desk/page.tsx` -- new, the `/desk` page (see What to Build + UI Evolution +
  Visual Requirements).
- `apps/frontend/lib/api.ts` -- add the 7 desk-screen/topup fetch/trigger/cancel functions.
- `apps/frontend/lib/types.ts` -- add:
  - `DeskScreenRow { symbol: string; side: "support"|"resistance"; band_class: "A"|"B"|"C"|null;
    distance_bps: number; band_score: number; price_low: number; price_high: number; coverage:
    Record<string, {has_bars: boolean; latest_window_end_utc: string|null}>; tick_evidence: boolean }`
  - `DeskScreenSkip { symbol: string; skipped: true; reason: "no_bars"|"no_basis"; coverage: {...};
    tick_evidence: boolean }`
  - `DeskScreenSnapshot { id, screen_date, as_of, universe_snapshot_id, config_fingerprint,
    bar_store_signature, created_utc, rows: DeskScreenRow[], skipped: DeskScreenSkip[] }`
  - `DeskScreenMeta` (the list-endpoint's lightweight projection: id/screen_date/as_of/
    universe_snapshot_id/config_fingerprint/bar_store_signature/created_utc/`counts:{rows,skipped}`)
  - `DeskScreenComputeSnapshot { id, state: "running"|"done"|"cancelled"|"failed", screen_date,
    started_utc, finished_utc, error, reused: boolean, screen_id: string|null, progress:
    {members_total, members_done, current: string|null} }`
  - `DeskTopupComputeSnapshot { id, state, started_utc, finished_utc, error, progress:
    {pairs_total, pairs_done, outcomes: [{symbol, timeframe, outcome: "reused"|"fetched"|"failed",
    detail: string|null}]} }`

## UI Evolution

- New user-facing capability: the operator can open a third page, `/desk`, click "Run Screen," watch
  it compute live, and read a dense ranked briefing (with full provenance) of which registered
  universe symbols have the closest tradable walls today — without visiting `/structure`
  symbol-by-symbol.
- New information displayed: the latest screen's ranked rows (symbol/side/band-class chip/
  distance-bps chip/band score/per-timeframe coverage badge/tick-evidence badge), honestly-grouped
  skipped members (`no_bars` vs `no_basis`), the screen's full provenance line (universe snapshot id
  + date, `as_of`, `config_fingerprint`, bar-store freshness labeled "window last requested"), a
  read-only screen-history list (date + rows/skipped counts + provenance summary), and live Run
  Screen / Top-up progress.
- New user actions: "Run Screen" (single-flight trigger, live progress, Cancel) and "Top-up"
  (single-flight trigger, live `pairs_done`/`pairs_total` progress, Cancel) — both new buttons on
  `/desk`. Top-up is the first-ever UI surface for the J-02 top-up compute manager (previously
  CLI/POST-only).
- UI surface changes: one new page, `/desk`, added as the third persistent top-nav entry (after
  Structure).
- Navigation changes: top nav becomes Cockpit · Structure · Desk, data-driven from `GET
  /meta/ui-routes` (`NavBar.tsx` needs no edit — it already renders whatever the endpoint serves).

## Visual Requirements

- Component patterns: reuse `Panel` (`components/Panel.tsx` — bordered `rounded-lg`
  `border-slate-800 bg-slate-900/60` section with an uppercase label) for each `/desk` section
  (briefing table, provenance, skipped members, screen history). Reuse `structure/page.tsx`'s local
  `EmptyState`, `LoadingPanel`, `UnavailablePanel`, and `NotComputedPanel` patterns verbatim in
  shape/testid convention rather than inventing new ones — `/desk`'s "not computed yet" state is the
  `NotComputedPanel` treatment (amber, headline + detail + Compute button), its degraded/unreachable
  state is `UnavailablePanel` (amber, "Nothing cached and nothing fabricated is shown in its place."
  register), and its populated table is a plain `Panel`.
- Layout: persistent `NavBar` (unchanged) + a single stacked-`Panel` main column matching
  `/structure`'s dense layout — not a dashboard grid. Order: provenance line panel, briefing table
  panel (ranked rows), skipped-members panel, screen-history panel, Run Screen / Top-up controls.
- Key visual effects: no new colors — dark-only slate base, emerald for active/positive (the Run
  Screen button and NavBar's active-link treatment), amber for not-computed/degraded states
  (`border-amber-800/60 bg-amber-900/20 text-amber-300`), a small pulsing emerald dot for live
  progress (`NotComputedPanel`'s `edge-report-compute-running` block is the exact pattern to mirror
  for both Run Screen and Top-up progress), monospace chips for band/distance/score values (the
  `Metric` component's `font-mono` convention).
- States to handle: (1) empty — no screen ever computed: exact text `"Desk screen not computed
  yet."` + enabled Run Screen button, rendered iff `latest === null`; (2) running compute — live
  progress, an in-flight second click observes the SAME job (no second POST), Cancel control; (3)
  populated — ranked rows + provenance + skipped grouping, rendered even when `rows` is empty but
  `skipped` is not (never conflated with state 1); (4) terminal states done/cancelled/failed mirror
  `NotComputedPanel`'s `isFailed`/`isCancelled` copy treatment; (5) backend-unreachable during a poll
  — keep the last known snapshot state, never fabricate one (mirrors `fetchEdgeReportCompute`'s
  `{ok:false, data:null}` fold).

## Key Test Scenarios

Browser QA must run against a FIXTURE-SCOPED backend (scope `TAPEOLOGY_DESK_UNIVERSE_DIR` /
`TAPEOLOGY_BAR_DIR` / `TAPEOLOGY_DESK_SCREEN_DIR` at a temp dir seeded with the committed 103-member
universe fixture + committed AAPL/MSFT bar fixtures, the `test_desk_screen_compute.py` `route_ctx`
pattern materialized as real files) — a screen against the real ambient store would render ~100
honest `no_bars` rows against 2-3 real ones, which is honest but not what the acceptance screenshots
need. `rm -rf apps/frontend/.next` + rebuild + restart both processes BEFORE any browser pass (T-9,
stale-build trap). Warm `tradability_cache` (see Backend list) before dispatching browser QA / replay.

- TC-1/TC-2/TC-3: empty state (`"Desk screen not computed yet."` + enabled Run Screen, screenshot) →
  click Run Screen (`POST .../screen/compute` fires with client's own today, single-flight refusal on
  a second click, screenshot) → terminal `done` renders ranked rows (chip copy "nearest same-class
  band") + honestly-grouped skipped members (screenshot).
- TC-4/TC-5: provenance line shows universe snapshot id+date, `as_of`, `config_fingerprint`, bar-store
  freshness labeled "window last requested" (never "last bar"), verbatim. Screen-history list shows
  each entry's date + rows/skipped counts from the meta-only `screens` list, no click interaction.
- TC-6: `GET /meta/ui-routes` returns exactly 3 entries in order (Cockpit, Structure, Desk); rendered
  nav shows the same (screenshot, present in every J-04 screenshot per DoD).
- TC-7/TC-8: a compute over an already-recorded 5-pin key resolves `reused: true` + the existing
  `screen_id`; a fresh compute resolves `reused: false` + its own new `screen_id`.
- TC-9: no universe registered → `POST .../screen/compute` 4xx, zero records before/after.
- TC-10: a corrupted universe snapshot file at a re-registered checksum → integrity error, bytes
  unchanged, no second file (mirrors the already-shipped `ScreenStore` test).
- TC-11/TC-12: single-flight (second concurrent POST → `started: false`, same job id); Top-up button
  → `POST /research/desk/topup/compute`, live `pairs_done`/`pairs_total`, Cancel → cancelling/
  cancelled state (screenshot).
- TC-13: `test_copy_discipline.py::test_lint_frontend_source_literals_are_clean` (unmodified) reports
  zero violations on the new `/desk` source — no advice/imperative/prediction language anywhere.
- TC-14/TC-17: `_select_best_band` and all five frozen research modules
  (`config.py`/`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`) show zero changed lines;
  `Config().config_fingerprint()` still `08e471b10130e1e2`.
- TC-15/TC-20: `test_meta_routes.py`'s widened 3-route assertions pass; full suite reports a
  non-decreasing pass count off the 1299-passed/8-skipped floor, zero new failures, and
  `desk_universe.py`/`desk_coverage.py`/`desk_topup_compute.py`/`desk_screen.py`'s existing tests all
  still pass unmodified except the two named new tests (corrupt-file guard, no-universe refusal).
- TC-16: J-07's `journey-scripts/J-07.json` step 8 passes within its own `20000` ms budget against the
  pre-warmed cache — treat a step-8-only failure with the LLM fallback passing as a golden
  false-negative to flag, not a J-07 regression.
- TC-18/TC-19: an all-skipped screen (`rows: []`, `skipped` non-empty) renders the empty ranked-rows
  section + skipped grouping, never the not-computed message. Page-load mount issues GETs only to
  `/research/desk/screen`, `/research/desk/screen/compute`, `/research/desk/topup/compute` — zero POST
  without an explicit button click.
- TC-21: backend-unreachable mid-poll keeps the last known snapshot, never fabricates one.
- J-07 regression walk (required-still-passing, full depth): sim cockpit `SIM-BUYER` settling Buyer
  Control; `/structure` Load for pinned AAPL as-of 2026-06-22 rendering the 300–302.4 wall; Case
  Studies drill-in; Edge Report honest state — each screenshotted, re-verified with the timeout fix +
  cache warm-up in place.

Definition of Done (from the phase spec, unabridged): J-04 passes via browser-qa-agent (3
screenshots per acceptance, nav visible in each); `GET /meta/ui-routes` lists exactly 3 routes;
J-01/J-02/J-03/J-07 remain green; no anti-goal violation; suite pass count non-decreasing off
1299/8-skip; dev handoff at `docs/handoffs/goal-desk-iter-4-dev.md`.
