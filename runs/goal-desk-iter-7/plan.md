# goal-desk-iter-7 Execution Plan

Environment: before running any test/build command, export
`TMPDIR=/var/tmp/iad.goal-desk-iter-7.822370 TMP=/var/tmp/iad.goal-desk-iter-7.822370 TEMP=/var/tmp/iad.goal-desk-iter-7.822370`.

## What to Build

- **J-06 — MCP contract v3 (15 → 17 tools).** Add `desk_universe` (`/research/desk/universe`) and
  `desk_screen` (`/research/desk/screen`) as no-required-argument static-path tools in
  `apps/backend/app/mcp/__init__.py`, mirroring the existing `datasets`/`setups`/`edge_report`
  shape exactly (`_STATIC_PATHS` entry + a `types.Tool(...)` registry entry with a description in
  the module's existing style). `get_endpoint`'s allowlist needs no change — `/research/desk/*` is
  already covered by the `/research/` prefix.
- **J-06 tests.** Extend `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` to 17 names
  (insert `desk_universe`, `desk_screen` — natural position is right after `edge_report`/before
  `pnl_ledger`, matching the era's "newest addition after its dependency sibling" convention, but
  exact placement is developer's call as long as the tuple is asserted verbatim). Add byte-identity
  tests for both new tools in BOTH the honest-empty state (no universe/screen ever registered —
  `{"snapshots": [], "latest": null, "integrity_errors": []}` / `{"screens": [], "latest": null,
  "integrity_errors": []}`) and a populated state, seeded directly via
  `UniverseStore(...).record(...)` / `ScreenStore(...).record(...)` (constructors take the store
  root dir; call `.record()` with the exact kwargs each store's `record()` method defines —
  `desk_universe.py:381` / `desk_screen.py:434`) into the live test backend's env-scoped store
  dirs — the same `BarStore.record()`-direct-seeding precedent already used for
  `bars`/`levels`/`tradability`/`setups` in this same file. Extend the module-scoped `backend_paths`
  fixture (`test_mcp_server.py:102`) with two new env keys, `TAPEOLOGY_DESK_UNIVERSE_DIR` and
  `TAPEOLOGY_DESK_SCREEN_DIR`, mirroring the existing `TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_DATASET_DIR`
  entries. Add one `get_endpoint` proxy test hitting `/research/desk/screen?date=...` — one
  matching date (returns `{"screen": <record>}` byte-identical to curl) and one non-matching date
  (returns `{"screen": null}`, `isError` false, never a 404).
- **J-06 guard test — F2 contract.** New sibling file of `apps/backend/tests/test_desk_ui_guards.py`
  (or an addition to it — developer's call) asserting `apps/frontend/app/desk/page.tsx`'s drill-in
  anchor(s) (`desk-row-drill-in`, `desk-skip-row-drill-in`) build their tooltip/`title` content from
  `row.distance_bps`, `row.band_score`, and each coverage entry's `latest_window_end_utc` — not a
  static or empty string — with a seeded-violation counter-test proving the check can fail (follow
  the existing `test_desk_ui_guards.py` source-introspection pattern: read the `.tsx` file as text,
  assert on substrings/structure, no browser).
- **F2 fix — consolidate lost hover tooltips onto the row's drill-in anchor.** In
  `apps/frontend/app/desk/page.tsx`, the `<Link data-testid="desk-row-drill-in" className="absolute
  inset-0">` (currently ~line 204-209) and `<Link data-testid="desk-skip-row-drill-in" ...>`
  (currently ~line 291-296) currently carry NO `title`, while the per-cell `title`s at
  `desk-row-distance`/`desk-row-score` (lines 225/228) and the `DeskCoverageBadges` per-badge
  `title` (line 146) are now hover-unreachable because the stretched anchor paints above them
  (iter-6 audit finding F2). Fix: give the drill-in anchor itself a composite `title` built from
  `row.distance_bps` (full precision), `row.band_score` (full precision), and each coverage entry's
  `latest_window_end_utc` (skip the anchor's per-cell titles or leave them as harmless dead code —
  developer's call, but the anchor's own title is what must be reachable). The skip-row anchor
  carries ONLY the coverage-freshness portion (no distance/score fields exist on a skip row — never
  fabricate one). **Zero change** to the anchor's `href`, `absolute inset-0` class, `data-testid`,
  or any other row markup — this is the hard constraint the spec chose this fix specifically to
  protect (`journey-scripts/J-05.json` step 4 clicks the whole `desk-screen-row` `<tr>`, and must
  keep landing on the anchor exactly as before).
- **Golden fix.** `runs/goal-session-desk/journey-scripts/J-05.json` step 2: change
  `{"testid": "desk-history-row"}` to a `{"css":
  "[data-testid=\"desk-history-row\"][data-screen-date=\"2026-06-22\"]"}` target (the `{"css":
  ...}` target type is already used elsewhere, e.g. `J-04.json` step 4) so replay selects by the
  row's own `data-screen-date` attribute (already present, `page.tsx:385`) instead of table
  position. No other step changes.
- **J-07 — full kept-product regression walk (browser-qa-agent).** This is a QA/browser-verification
  task, not a dev task — no new code is implied beyond what J-06/F2 above already produce. The
  browser-qa-agent must capture, with real screenshots (T-9 clean rebuild first: `rm -rf
  apps/frontend/.next` + restart both `:8301`/`:3301` processes; warm `/research/setups` +
  `/structure` Load once before timing anything):
  1. Sim cockpit: `SIM-BUYER` watched, "Buyer Control" panel settled — screenshot.
  2. `/structure` Load for pinned AAPL as-of `2026-06-22T21:00:00Z` (the 300-302.4-region wall
     renders) — screenshot.
  3. Case Studies drill-in (testids under `case-studies-row` / `case-studies-row-*`, Panel "Case
     Studies — drill-in" ~`page.tsx:750`) opened and rendering — screenshot.
  4. Edge Report panel (testids `edge-report-*`, register ~`page.tsx:977`) in its honest
     computed-or-not-computed state, no fabricated cell — screenshot.
  5. Kept-route byte-identity: per-route `curl --max-time` against `/`, `/structure`,
     `/meta/ui-routes`, `/research/taxonomy` compared byte-for-byte to the era-open baseline
     capture.
  6. Nav = exactly 3 routes (Cockpit/Structure/Desk); MCP = exactly 17 tools
     (`python -c 'import app.mcp; print(len(app.mcp.TOOL_NAMES))'`).
  7. Cumulative era diff has zero out-of-inventory changes.
  8. Fresh capture proving the F2 fix's composite tooltip is hoverable AND the row's click still
     navigates to `/structure?symbol=&asof=` exactly as before (TC-8/TC-9/TC-10).
- **Regression replay for J-01–J-05** (deterministic golden replay + LLM fallback where needed),
  re-verified specifically against the F2 change (J-04/J-05 golden scripts + a fresh browser pass).

## Agents Required

- backend-data: yes -- J-06 MCP tool additions + `test_mcp_server.py` extension + the new F2
  source-introspection guard test with its counter-test.
- frontend-ux: yes -- the F2 tooltip-consolidation fix on `apps/frontend/app/desk/page.tsx`
  (zero-geometry-change) and the `J-05.json` golden selector fix (test asset, not app code, but
  touched by the same pass).

## Frontend Present: yes

(No new page/nav/button. The F2 fix changes hover-affordance placement inside an already-shipped
page, and J-07 is a full kept-product browser walk — both require the QA agent's Chrome MCP checks.)

## Files to Create/Modify

- `apps/backend/app/mcp/__init__.py` -- add `desk_universe`/`desk_screen` to `_STATIC_PATHS` + two
  new `types.Tool(...)` entries in `TOOLS`.
- `apps/backend/tests/test_mcp_server.py` -- `EXPECTED_TOOLS` grows to 17; new byte-identity tests
  (empty + populated) for both new tools; `backend_paths` fixture gains
  `TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_DESK_SCREEN_DIR`; new `get_endpoint` proxy test for
  `/research/desk/screen?date=` (match + non-match).
- New test file (sibling of `apps/backend/tests/test_desk_ui_guards.py`) -- F2 tooltip-composition
  guard test + seeded counter-test.
- `apps/frontend/app/desk/page.tsx` -- composite `title` on `desk-row-drill-in` /
  `desk-skip-row-drill-in` anchors built from `distance_bps`/`band_score`/coverage
  `latest_window_end_utc`; no other markup change.
- `runs/goal-session-desk/journey-scripts/J-05.json` -- step 2 target becomes a date-qualified CSS
  selector.
- `docs/handoffs/goal-desk-iter-7-dev.md` -- dev handoff (required by Definition of Done).

## UI Evolution

- New user-facing capability: none. This iteration repairs a hover-honesty regression and adds a
  machine-readable (MCP) surface; no new page/panel/button.
- New information displayed: none new. The full-precision distance/score/coverage-freshness detail
  that briefly became hover-unreachable is restored via the row's existing hover affordance
  (consolidated on the drill-in anchor instead of per-cell).
- New user actions: none on `/desk` itself. A Claude conversation via MCP gains two new read-only
  tool calls (`desk_universe`, `desk_screen`).
- UI surface changes: none visible -- only WHICH element carries the hover tooltip changes (the
  row's single drill-in anchor, not individual cells).
- Navigation changes: none.

## Visual Requirements

- Component patterns: none new -- reuse the existing `<tr>`/stretched-`<Link>` row pattern
  byte-unchanged; only the `title` attribute placement moves.
- Layout: unchanged -- no layout edit in scope.
- Key visual effects: none new. The fix must be invisible until a hover actually happens (no visual
  diff at rest).
- States to handle: hovering a ranked row (full composite tooltip incl. distance/score/coverage);
  hovering a skipped row (coverage-only tooltip, no fabricated distance/score); the kept-product
  states J-07 walks (cockpit Buyer Control settled, Structure loaded/wall rendered, Case Studies
  drill-in populated, Edge Report honest computed-or-not-computed).

## Key Test Scenarios

- TC-1..TC-7: `test_mcp_server.py` -- `desk_universe`/`desk_screen` byte-identical to curl in empty
  AND populated fixture states; `list_tools()` returns exactly 17 names matching `EXPECTED_TOOLS`;
  `get_endpoint` on `/research/desk/screen?date=` proxies verbatim for a match and returns the
  honest `{"screen": null}` (not an error) for a non-match.
- TC-8..TC-11: hovering any ranked row's drill-in anchor shows the full unrounded `distance_bps`,
  full `band_score`, and each populated timeframe's exact freshness value; the anchor's `href`,
  `absolute inset-0` class, and `data-testid` are byte-unchanged from iter-6, and clicking anywhere
  in the row still navigates to `/structure?symbol=<sym>&asof=<iso>` exactly as J-05 already
  verified; a skipped row's tooltip includes only the coverage fields that exist, never a fabricated
  distance/score; the new guard test (with its counter-test) enforces this composition.
- TC-12: `J-05.json` step 2 selects the row whose `data-screen-date="2026-06-22"`, not the first
  match; replay against a freshly-seeded backend still reaches "Viewing the recorded screen for
  2026-06-22".
- TC-13..TC-16: real-browser Buyer Control settling; `/structure` Load for pinned AAPL as-of
  2026-06-22 (300-302.4 wall); Case Studies drill-in renders; Edge Report honest panel renders; kept
  routes byte-identical to the era-open baseline.
- TC-17: full backend suite >= 1341 collected / 1333 passing / 8 skipped floor (plus new tests),
  0 failures; `Config().config_fingerprint()` == `08e471b10130e1e2`.
- TC-18: J-01-J-05 all re-verify their already-recorded acceptance states (no regression) via
  deterministic replay or LLM fallback.

## Notes for downstream agents

- Do NOT touch `desk_screen.py`'s CLI write-path guard, `bars.py`'s `_has_finite_prices` filter, the
  loosened `test_structure_chart_viewport.py:194` assertion, `StructureChart.tsx`, `PriceChart.tsx`,
  `app/engine/`, any new `Config` field, or any new backend route -- all explicitly out of scope
  this iteration; none of their files should be opened.
- The F2 fix must NOT raise any cell's `z-index`/`pointer-events`, must NOT add a row-level
  `onClick`/`router.push`, and must NOT change what element is topmost at the row's centre point --
  any of those would risk silently breaking `journey-scripts/J-05.json` step 4's already-passing
  click on `desk-screen-row`. This is the one reason a "put the title back on the covered cell" fix
  was rejected in favor of consolidating onto the anchor.
- If J-06 and J-07 both land clean this iteration, all 7 journeys are passing -- the next dispatch
  after this phase should be the goal-evaluator's own `GOAL_ACHIEVED` assessment, not a manufactured
  8th journey.
