# Phase goal-desk-iter-7 — UX Regression Review

**Date:** 2026-07-26

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

| Capability | Navigation path from home | Clicks | Visual feedback | Assessment |
|---|---|---|---|---|
| `desk_universe` MCP tool (Claude-readable universe snapshots) | None on the web UI — reachable only from a Claude conversation with this project's MCP server connected | N/A (not a browser surface) | The tool call's returned JSON is the only "feedback"; no UI affordance exists or is claimed | Intentionally backend-only. Matches the era's own Blueprint conformance table, which already classifies MCP tools as "no page" — the same treatment given to all 15 prior tools (`datasets`, `bars`, `levels`, `tradability`, `setups`, `edge_report`, etc.). `desk_universe` proxies data `/desk`'s Provenance panel already renders on the web page; no redundant UI surface is missing, none was warranted. Not flagged. |
| `desk_screen` MCP tool (Claude-readable screen ledger) | Same — Claude/MCP conversation only | N/A | Same | Same reasoning — `/desk`'s Briefing/Skipped Members/Screen History panels already show this exact data in the browser. Not flagged. |
| Composite hover tooltip on a ranked `/desk` row (`desk-row-drill-in` anchor) | Already-reached `/desk` page (1 click from home via `NavBar`) → hover anywhere inside a ranked row | 0 clicks, hover-only | Native browser tooltip appears on hover, verified live: `UT-02` confirms the AAPL row's anchor `title` reads `distance 0.33523150389608725 bps · score 97 · 1h window last requested: 2026-07-23 · ...` byte-for-byte, triggered from the "side" cell (not the number cells themselves) | Discoverable. This is a repair, not a new capability — the detail existed before iter-6 broke its hover-reachability; iter-7 restores it and *widens* the reachable area from a few small cells to the entire row. |
| Composite hover tooltip on a skipped `/desk` row (`desk-skip-row-drill-in` anchor) | Same `/desk` page → hover anywhere inside a skipped row | 0 clicks, hover-only | `UT-03` confirms the ABBV row's tooltip reads only the four timeframe "window last requested" lines, with no "distance"/"score" substring present | Discoverable and honest — no fabricated field for data that does not exist on a skip row. |

No new page, panel, button, or nav entry was added, and none was needed. `apps/frontend/components/NavBar.tsx` and `apps/backend/app/meta.py`'s `UI_ROUTES` are confirmed byte-unchanged this iteration (`git diff`/`git status` show no diff on either file; `UT-12` independently confirms exactly 3 nav links — Cockpit/Structure/Desk — live in the browser).

## Regression Risk

| Shared component | Prior feature(s) it serves | This iteration's change | Risk level | Evidence it still works |
|---|---|---|---|---|
| `apps/frontend/app/desk/page.tsx` — `desk-row-drill-in` / `desk-skip-row-drill-in` anchors | J-04 (Briefing/Skipped Members tables), J-05 (whole-row click-through to `/structure?symbol=&asof=`) | Added a `title={deskRowDrillInTitle(row)}` / `title={deskSkipDrillInTitle(skip)}` attribute to each anchor. Confirmed via `git diff`: this is the *entire* code diff to this file — no other JSX attribute touched. | Low. The change is additive to a single attribute that has no effect on layout, hit-testing, or navigation. | `UT-04`/`UT-05` confirm `href` and `className="absolute inset-0"` are byte-unchanged from iteration 6 and that clicking anywhere in a ranked or skipped row (not just the symbol text) still navigates to `/structure?symbol=<sym>&asof=<iso>` exactly as J-05 verified. `UT-J-04`/`UT-J-05` (both the merged results and the standalone deterministic-replay report) re-ran the full J-04/J-05 golden scripts end-to-end with all expects holding. `UT-06` confirms the row is visually byte-identical at rest (no tooltip visible, no layout shift) — the fix is genuinely invisible until a hover occurs. |
| `runs/goal-session-desk/journey-scripts/J-05.json` (golden test asset) | J-05's own regression replay | Step 2's click target changed from positional `{"testid": "desk-history-row"}` to the date-qualified `{"css": "[data-testid=\"desk-history-row\"][data-screen-date=\"2026-06-22\"]"}`, per iter-6 audit finding T1. | Not a UI regression — a latent test-harness selector bug fixed before it could cause a false pass/fail on a future multi-history-row fixture. | `UT-J-05` passed after the fix (both merged results and standalone replay report), reaching "Viewing the recorded screen for 2026-06-22" by selecting the correct row via `data-screen-date`. |
| `runs/goal-session-desk/journey-scripts/J-07.json` (golden test asset) | J-07's own kept-product sentinel | Step 10's assertion target corrected from `tradable-map-chart-caption` (a static candle-merge description that never contained `300.11`) to `tradable-map-table` (which does). | Not a UI regression — a pre-existing false assertion in the golden script, caught and fixed this iteration (disclosed honestly in `UT-09`'s "Deviation" note rather than silently patched over). | `UT-09` confirms the Tradable Map table row `resistance 300.11–302.2 Class A ...` renders and the canvas shows real candles with the price-band overlay. |
| `apps/backend/app/mcp/__init__.py` (`_STATIC_PATHS`, `TOOLS`) | The 15 existing MCP tools (J-01 through the edge-report era) | Purely additive: two new dict/tuple entries. No existing tool's path, schema, or description was edited (confirmed via `git diff` — only two new blocks added). | Low. | Full `test_mcp_server.py` suite (34 tests) passes, including every pre-existing tool's byte-identity/allowlist/honest-404 assertions, none of which needed a code change to keep passing. |
| `apps/frontend/app/structure/page.tsx`, `apps/backend/app/research/desk_screen.py` (CLI guard), `bars.py`, `StructureChart.tsx`, `PriceChart.tsx` | Structure page (era `structure_ui`/`tradable_wall`/`fast_wall`/`clean_slate`/`yahoo_fetch`), Cockpit chart | None — not opened this iteration (confirmed by dev handoff's explicit "not touched" list and the plan's out-of-scope guard). | N/A (untouched). | `UT-08` (Buyer Control settles), `UT-09` (Structure Load + wall renders), `UT-10` (Case Studies drill-in), `UT-11` (Edge Report honest state) — the three screenshots J-07 had been missing since iteration 4 are now captured, closing that standing gap with real evidence, not just an unopened-file inference. |

One evidence gap worth surfacing, not a regression: the QA test plan's TC-17 ("kept routes byte-identical to the era-open baseline") was **skipped** because the era-open baseline snapshot artifact is not available for diffing (`reports/qa/goal-desk-iter-7-qa.md` discloses this openly rather than fabricating a pass). This is a literal-acceptance-criterion gap, not a discovered defect — none of the files backing `/`, `/structure`, `/meta/ui-routes`, or `/research/taxonomy` were touched this iteration, and the functional-equivalent checks (`UT-08`–`UT-12`, J-01–J-05 all passing) independently confirm those same routes still render and behave correctly. Residual regression risk is low; the gap is a QA-lane completeness note for a future iteration to restore an era-open baseline artifact, not evidence of breakage.

## UI vs Backend Parity

- `desk_universe`/`desk_screen` are explicitly, consistently documented as backend/MCP-only across all three source artifacts (`implementation-summary.md`'s "Backend-Only Items", `user-visible-changes.md`'s "Not Visible Yet", and the phase spec's own "New user-facing capability: None" + "Blueprint conformance" sections) — no discrepancy between what was claimed built and what was claimed visible.
- This is a legitimate backend-only case, not a stranded capability: both tools proxy data the `/desk` web page has already rendered since iteration 4 (Provenance panel, Briefing/Skipped Members/Screen History). Adding a redundant web-UI surface for data already on-screen would not have served any operator who isn't already using Claude/MCP; the phase spec's own reasoning ("the goal was to make the data Claude-readable, not to add a redundant UI surface for data the page already shows") holds.
- No new backend value was introduced this iteration beyond the two MCP proxies — "Data-contract additions: None" is accurate (confirmed: no new `Config` field, no new route, no new computed value).
- The hover-honesty fix has no backend counterpart to check for parity — it is a pure frontend repair of data that was always served correctly by the backend; the regression was in the DOM's hover-reachability, not the data.

## Flags

### Hidden Capabilities
- None found.

### Undiscoverable Capabilities
- None found. The two new MCP tools are appropriately backend-only (see UI vs Backend Parity above) rather than undiscoverable — they were never intended to have a browser navigation path, and the existing 15-tool precedent in this same codebase establishes that MCP tools are not expected to have one.

### Potential Regressions
- None confirmed. The one shared, previously-shipped file this iteration edited (`apps/frontend/app/desk/page.tsx`) has a single-attribute diff (`title={...}` on two anchors) with dedicated before/after evidence proving click geometry, layout, and at-rest appearance are byte-unchanged (`UT-04`, `UT-05`, `UT-06`), plus passing full-journey replays for both features that own that file (`UT-J-04`, `UT-J-05`).
- Soft note: TC-17's kept-route byte-identity diff was skipped for lack of a baseline artifact (see Regression Risk table) — functionally covered by other passing evidence, but the specific literal acceptance criterion from the DoD/plan is not independently proven this iteration.

### Visual Consistency
- No new visual style was introduced. The only DOM change is a `title` attribute, which is invisible at rest and renders as the browser's own native tooltip on hover — there is nothing to compare against the DESIGN SYSTEM tokens because nothing about color, spacing, typography, or effects changed.
- `UT-06` (rest-state screenshot) confirms the page's dense/dark/monospace-numeric-cell house style is unchanged; `UT-01` confirms all four panels (Provenance/Briefing/Skipped Members/Screen History) still render in their established order and style.
- Consistent with the precedent set by the iter-6 UX regression review, which already established this page's "hover-only affordance, no persistent icon" convention as intentional and matching the rest of the app — iter-7 does not deviate from or worsen that convention, it repairs a regression within it.

## Recommendation

No action required. All new capabilities are either fully discoverable on the already-reached `/desk` page (the restored hover tooltips) or are intentionally backend/MCP-only surfaces consistent with this era's own established pattern and explicitly disclosed as such in every relevant artifact. The one shared component touched (`/desk/page.tsx`) has a minimal, well-evidenced diff with no regression found in either of the two features that depend on it (J-04, J-05). The single QA-completeness gap (TC-17's missing era-open baseline for a literal byte-identity diff) is worth restoring in a future iteration but does not indicate an actual defect given the strength of the functional-equivalent evidence already collected.
