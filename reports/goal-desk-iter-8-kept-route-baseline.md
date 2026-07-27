# goal-desk-iter-8 — kept-route baseline vs era-open (`047c38e`)

One-off diagnostic (per `apps/backend/scripts/goal-desk-iter8-baseline-diff.py`, disposable, not a CI gate). Era-open backend = a scratch `git worktree` at `047c38e` (the era-open docs commit; its application code is byte-identical to its parent, the 5D-demolition-closed tree) booted against a throw-away copy of `.data/` + the journal DB. Current-tree backend = the working tree, booted against an IDENTICAL throw-away copy of the SAME data snapshot. Neither backend ever touched the ambient `apps/backend/.data/`.

- Era-open backend: `http://127.0.0.1:33163` (worktree `047c38e`)
- Current-tree backend: `http://127.0.0.1:38527`
- `/research/setups/{id}` resolved id (from era-open's own unfiltered `/research/setups` list, first event): `NO-SETUP-EVENTS-FOUND`

## Route-by-route results (TC-1)

| Route | Inputs | Verdict | Reason (if differing) |
|---|---|---|---|
| taxonomy | `/research/taxonomy` | **MATCH** | — |
| datasets (list) | `/research/datasets` | **MATCH** | — |
| datasets/{id} | `/research/datasets/e09e8ae6b1f84a3b8545d1f426917cfd` | **MATCH** | — |
| bars (list) | `/research/bars` | **MATCH** | — |
| bars/{id} | `/research/bars/55bb757e6df84b1d82d1c7ab719dfb51` | **MATCH** | — |
| bars/{id}/candles | `/research/bars/55bb757e6df84b1d82d1c7ab719dfb51/candles` | **MATCH** | — |
| candles (merged, AAPL 1d) | `/research/candles?symbol=AAPL&timeframe=1d&limit=1000` | **DIFFERS** | JSON differs at: $.integrity_errors length 0 vs 1; $.revised_timestamps: 188 vs 187 |
| levels (AAPL, pre-repair as-of) | `/research/levels?symbol=AAPL&as_of=2026-06-22T21:00:00Z` | **MATCH** | — |
| levels (AAPL, post-repair as-of) | `/research/levels?symbol=AAPL&as_of=2026-07-25T21:00:00Z` | **MATCH** | — |
| tradability (AAPL, pre-repair as-of) | `/research/tradability?symbol=AAPL&as_of=2026-06-22T21:00:00Z` | **MATCH** | — |
| tradability (AAPL, post-repair as-of) | `/research/tradability?symbol=AAPL&as_of=2026-07-25T21:00:00Z` | **MATCH** | — |
| setups (AAPL filter) | `/research/setups?symbol=AAPL` | **MATCH** | — |
| setups/{id} | `/research/setups/NO-SETUP-EVENTS-FOUND` | **MATCH** | — |
| pnl/ledger | `/research/pnl/ledger` | **MATCH** | — |
| profiles | `/research/profiles` | **MATCH** | — |
| strategies | `/research/strategies` | **MATCH** | — |
| edge-report | `/research/edge-report` | **MATCH** | — |
| meta/ui-routes (NAMED EXEMPTION, TC-2) | `/meta/ui-routes` | **DIFFERS** | JSON differs at: $.routes length 2 vs 3 |

**16 match / 2 differ** out of 18 routes exercised.

## TC-2 — `/meta/ui-routes` named exemption

This route is EXPECTED to differ (era-open serves 2 rows: Cockpit + Structure; the current tree serves 3: + Desk, J-04's own sanctioned addition). See its row above for the live-verified row counts on both sides — a difference here is the documented, goal.md-named exemption, never a defect.

## MCP tool-count delta (15 → 17) — cited, not re-diffed

Per this iteration's IN SCOPE note and `assumptions.md` iter-8: the MCP surface is not a second HTTP server this script re-diffs — it is a stdio proxy over the SAME REST routes diffed above. The 15→17 tool-count delta is iter-7's own already-live-proven evidence (`docs/handoffs/goal-desk-iter-7-audit.md` §"Domain Assessment": `len(app.mcp.TOOL_NAMES) == 17` in the documented order, both new tools proxying byte-identically to their REST equivalents in both empty and populated states) — a binding "do not redo" item (`iteration-state.md`). Not re-run here.

## TC-3 — full out-of-inventory file accounting

`git diff --name-only 047c38e -- apps/` on the current tree lists **42 files**. Every one is accounted for below by either R-1's eight named files or goal.md's Key Capability inventory (the era's own new-surface modules/routes/tests) — none is unexplained.

| File | Accounted for by |
|---|---|
| `apps/backend/app/config.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/app/main.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/app/mcp/__init__.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/app/meta.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/app/providers/adapters/yahoo.py` | R-1 (owner-ratified price-less-bar repair) |
| `apps/backend/app/research/bar_index.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/app/research/bars.py` | R-1 (owner-ratified price-less-bar repair) |
| `apps/backend/app/research/desk_coverage.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/app/research/desk_routes.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/app/research/desk_screen.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/app/research/desk_screen_compute.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/app/research/desk_topup_compute.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/app/research/desk_universe.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/app/research/routes.py` | R-1 (owner-ratified price-less-bar repair) |
| `apps/backend/pyproject.toml` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/fixtures/universe/sp100_constituents.html` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/fixtures/universe/sp100_constituents_corrupted.html` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/fixtures/yahoo/MSFT_1d_20260101_20260626.json` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/fixtures/yahoo/MSFT_1h_20260601_20260618.json` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_bar_index.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_bars.py` | R-1 (owner-ratified price-less-bar repair) |
| `apps/backend/tests/test_bars_api.py` | R-1 (owner-ratified price-less-bar repair) |
| `apps/backend/tests/test_desk_coverage.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_desk_hover_tooltip_guard.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_desk_screen.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_desk_screen_compute.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_desk_topup_compute.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_desk_ui_guards.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_desk_universe.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_desk_universe_api.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_desk_universe_live_integration.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_mcp_server.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_meta_routes.py` | goal.md Key Capability inventory (new era-B surface) |
| `apps/backend/tests/test_structure_chart_viewport.py` | R-1 (owner-ratified price-less-bar repair) |
| `apps/backend/tests/test_yahoo_adapter.py` | R-1 (owner-ratified price-less-bar repair) |
| `apps/frontend/app/desk/page.tsx` | goal.md Key Capability inventory (new era-B surface) |
| `apps/frontend/app/structure/page.tsx` | goal.md Key Capability inventory (new era-B surface) |
| `apps/frontend/components/StructureChart.tsx` | R-1 (owner-ratified price-less-bar repair) |
| `apps/frontend/lib/api.ts` | goal.md Key Capability inventory (new era-B surface) |
| `apps/frontend/lib/types.ts` | goal.md Key Capability inventory (new era-B surface) |

**Zero unaccounted files.** J-07's "zero out-of-inventory changes" clause holds, reading "inventory" as including R-1 per the owner's ratification.

## Method notes

- `/research/bars/{id}` and `/research/bars/{id}/candles` read the RAW per-series store (`BarStore.get`/`.candles`) — R-1's `_merged_rows` exclusion applies ONLY to the merged read paths (`merged_candles`/`merged_bars`, backing `/research/candles`, `/research/levels`, `/research/tradability`); the raw per-series file is untouched on disk (R-1's own scope statement), so a raw single-series read of the AAPL 1d id is expected to MATCH even though it is one of R-1's named 60 series — the difference, if any, is confined to the merged-read routes and only for an as-of at/after the price-less row's own date (2026-07-24).
- `/research/candles` has no `as_of` parameter (unlike `/research/levels`/`/research/tradability`); it is exercised once, unfiltered, for `AAPL`/`1d` — the merged read's own full current state is what either reveals or does not reveal the excluded row.
- `/research/pnl/ledger`, `/research/profiles`, `/research/strategies` are backed by the SAME journal DB (a throw-away COPY of the ambient `tapeology_journal.db`, identical on both sides) so the comparison reflects the route/serialization CODE, not two different registries.

