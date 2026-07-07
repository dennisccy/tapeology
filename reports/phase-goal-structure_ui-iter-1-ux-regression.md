# Phase goal-structure_ui-iter-1 — UX Regression Review

**Date:** 2026-07-07

**Verdict:** UX-REGRESSION-FAIL

<!-- One of the five DoD-required honest-state acceptance screenshots (the "levels-but-no-zones"
     state) is confirmed broken: the chart panel renders as a fully blank box, not the required
     "level lines still visible" honest state. Everything else this iteration built — nav
     discoverability, three of four honest states, the populated chart+table, regression safety —
     is solid. See "Flags > Broken Capability" for the full evidence chain. -->

## New Capability Discoverability

| New capability | Navigation path | Clicks from home | Verdict |
|---|---|---|---|
| `/structure` page itself | Top-bar "Structure" link, present on every page (`NavBar`, data-driven from `GET /meta/ui-routes`) | 1 | Discoverable |
| Symbol + as-of query controls | Directly on the `/structure` page, above the fold, in a labelled form | 0 (already visible on arrival) | Discoverable |
| Price chart with S/R level lines | Renders automatically after Load, inside the "Price chart — S/R levels" panel | 1 (Load click) | Discoverable when data exists — **broken in one state, see Flags** |
| Confluence-zones table (A/B/C) | Renders automatically after Load, inside the "Confluence zones" panel, directly below the chart | 1 (Load click) | Discoverable |
| Four honest states (no-series / no-levels / no-zones / degraded) | Same page, same Load action — the state itself IS the page's content, not a separate destination | 1 (Load click) | 3 of 4 fully discoverable; 1 of 4 (no-zones) has a broken sub-element — see Flags |

The nav entry itself is exemplary: `apps/frontend/components/NavBar.tsx` has zero hardcoded route list (verified by reading the file directly) — it fetches `GET /meta/ui-routes` and renders whatever `nav: true` entries come back, with an honest `navigation unavailable — backend unreachable` fallback if the fetch fails. The backend's one-line additive change to `UI_ROUTES` in `apps/backend/app/meta.py` is the entire mechanism; browser QA (UT-04) independently confirmed via `grep -rn 'href="/structure"'` that no client file hardcodes the link. This is the single-source-of-truth nav pattern working exactly as designed — no discoverability flag warranted.

Label clarity: "Structure" is a slightly abstract label for a non-technical user (it doesn't say "Support/Resistance Levels"), but it matches the term used consistently throughout `docs/goal.md`, the phase spec, and the page's own header/framing copy ("Deterministic support/resistance levels and A/B/C confluence zones..."), so there is no drift between the nav label and what the page actually shows. Not flagged as label confusion.

## Regression Risk

Per the UI Regression Scout method: cross-referencing this phase's changed-files list (`git diff --stat`, corroborated against the ui-surface-map) against components long-established by prior sessions (`i_will_be_super_rich_with_my_loved_ones` / `i_will_be_super_rich` / `i_will_be_rich`, which built the Cockpit, Journal, Studies, Performance pages and their shared components):

| Shared component | Prior feature it serves | This phase's touch | Risk |
|---|---|---|---|
| `apps/backend/app/meta.py` `UI_ROUTES` | Nav for **every** page (all prior journeys) | Additive tuple entry only (`git diff` shows a single `+1` line; the 5 pre-existing entries are untouched, in the same order) | Low — confirmed byte-identical by both my own diff read and browser QA (UT-04, UT-13) |
| `apps/frontend/components/NavBar.tsx` | Site-wide nav | Not modified (0 lines changed) — new link appears purely because the data it reads grew | None |
| `apps/frontend/components/SymbolSearch.tsx` | Studies page's `StudyCreateForm.tsx`, Cockpit's `TopBar.tsx` ticker input | Reused verbatim, 0 lines changed | None — same untouched component, new consumer |
| `apps/frontend/lib/api.ts` / `lib/types.ts` | Every page's data fetching | Additive only (new exports appended; `git diff` shows pure insertions, no existing function/type edited) | Low |
| `apps/frontend/components/Panel.tsx` (`Panel`, `EmptyHint`) | Every Cockpit panel (`QuotePanel`, `TapeStatePanel`, `FeaturesPanel`, `ObservationsPanel`, `RecentTradesPanel`, `EventLogPanel`, `ProviderUnavailable`) plus `PriceChart.tsx` and `/performance`/`/studies` | Not modified; `EmptyHint` itself is a plain unstyled `<p>` — confirmed blameless by reading `Panel.tsx` directly | None |
| `apps/frontend/components/PriceChart.tsx` (Cockpit's chart, serves the SIM-BUYER/SIM-SELLER journeys) | Cockpit home page | **Not touched at all** — the new `StructureChart.tsx` is a separate file that follows PriceChart's pattern rather than reusing it, exactly as the plan specified | See advisory note below |

Direct regression testing already ran and passed: UT-13 re-verified all four pre-existing pages (`/`, `/journal`, `/studies`, `/performance`) render their original content unchanged with the 5-link nav; UT-14 re-ran the Cockpit's SIM-BUYER watch flow end-to-end (quote, trades, features, tape state, event log, resolving to `buyer_control`) with no change from pre-iteration behavior. Both PASS. **No regression is observed in any prior journey.**

**Advisory (not a confirmed regression, but worth a follow-up look):** I read `StructureChart.tsx` and `PriceChart.tsx` side by side. Both wrap their `lightweight-charts` canvas in an identical structure — a `position:relative` container holding (a) the chart's mount div, which `lightweight-charts` populates internally with `position:absolute` canvases at explicit `z-index:1`/`z-index:2`, and (b) a sibling empty-state hint `<div className="pointer-events-none absolute inset-0 ...">` wrapping `EmptyHint`, with no explicit `z-index` (defaults to `auto`). Per CSS stacking rules, a positioned descendant with an explicit z-index always paints over a sibling positioned descendant at `z-index: auto`, regardless of DOM order — which is exactly the mechanism browser QA identified as the root cause of the UT-10 failure (see Flags below). Because `PriceChart.tsx` (the Cockpit's chart, serving the required-still-passing J-04 journey) uses the **identical** markup shape for its own `"Loading price history…"` / `"No price history for this window yet"` hints, the same occlusion is likely to affect it too, whenever its chart has been mounted but has zero bars. This iteration's regression testing (UT-14) only exercised the Cockpit chart's **populated** state, not its loading/empty state, so this was not directly tested either now or, as far as I can tell from the available handoffs, previously. This is not caused by this phase's edits (the file is untouched) — it is a pre-existing latent pattern that this phase's new component faithfully copied, and this phase's unusually rigorous pixel-level QA is what surfaced it as a real defect for the first time. Recommend a follow-up check of the Cockpit's own chart during its loading/empty window, and fixing the z-index issue once, consistently, in both components (or in a shared chart-wrapper), rather than only in `StructureChart.tsx`.

## UI vs Backend Parity

| Backend capability (era-4 structure stack) | Surfaced in UI this iteration? | Assessment |
|---|---|---|
| S/R levels (`GET /research/levels`) — price/timeframe/type | Yes — chart price lines | Full parity |
| Confluence zones — class/score/members (`GET /research/levels`) | Yes — zones table | Full parity |
| Recorded bar series (`GET /research/bars`) | Yes — chart candles | Full parity |
| `SrLevel.touch_count` / `SrLevel.strength` (present in the API response, captured in `lib/types.ts`) | No — neither the chart line label nor the zones table shows these two fields | Not a gap: the phase spec's own DoD and Testing Requirements only call for price/timeframe/type on lines and price/timeframe/score/class on the table — `touch_count`/`strength` were never in this iteration's scope |
| Strategy registry (`GET /research/strategies`, `GET /research/profiles`) | No | **Intentional, documented deferral** — explicitly out of scope for J-01, targeted at J-02 per `docs/goal.md`'s dependency order (J-01→J-02→J-03), stated identically in the phase spec, the plan, `user-visible-changes.md`'s "Not Visible Yet" section, and the dev handoff's "Suggested Next Steps" |
| Backtest comparison (`structure_tape` vs `v1`) | No | **Intentional, documented deferral** — same reasoning, targeted at J-03 |
| `/datasets` library-inventory view | No | **Explicitly out of scope for this entire interlude** (roadmap Card 5.9), not just this iteration |

No parity gap is flagged. Every value this iteration's own DoD requires is surfaced verbatim; the deferred capabilities (registry, comparison) are consistently and explicitly documented as future sections of this SAME page across every artifact I read (plan, spec, user-visible-changes, dev handoff) — this is a genuine phased build-out, not backend work silently outpacing the UI.

## Flags

### Hidden Capabilities
None. The `/structure` page, its controls, its chart, and its zones table all have a clear, data-driven, 1-click navigation path, confirmed by browser QA and by my own reading of `NavBar.tsx`.

### Undiscoverable Capabilities
None.

### Potential Regressions
None confirmed. See "Regression Risk" table above — all touched shared surfaces (`meta.py` `UI_ROUTES`, `api.ts`, `types.ts`) are additive-only, and the two pre-existing components most load-bearing for prior journeys (`NavBar.tsx`, `SymbolSearch.tsx`) are byte-unchanged. The one advisory item (the shared `EmptyHint`-occlusion pattern possibly also present in `PriceChart.tsx`) is not this phase's introduced regression — it is a pre-existing pattern this phase's new code copied and, in copying, proved buggy. Flagged above for a follow-up check, not as a confirmed regression.

### Broken Capability
- **The "levels exist but no qualifying zone" honest state does not show its required chart content.** Per the phase's own DEFINITION OF DONE (item e) and the "Honest UI states only" critical anti-goal ("no fabricated chart... every failure mode surfaces an explicit, distinct state"), when `confluence_zones` is empty but `levels` is non-empty, the chart panel is supposed to keep showing the 3 (in the tested case) dashed level lines while only the zones panel shows its own distinct empty message. Browser QA (`UT-10`, FAIL) found the zones-panel message renders correctly, but the chart panel itself renders as a **fully blank box** — I opened `reports/qa/goal-structure_ui-iter-1-evidence/UT-10-no-zones.png` directly and confirmed this visually: no candles (expected, there are none), but also **no dashed level lines and no fallback "no recorded candle series" hint text** — just the chart's empty grid and border, indistinguishable from a broken page. By contrast, the populated-state screenshot (`UT-06-populated-chart.png`) shows the same panel working correctly with candles, price lines, and axis labels when data exists.
  - Root cause (confirmed by browser QA's `getComputedStyle`/pixel-scan and independently sanity-checked by me by reading `StructureChart.tsx` lines 96-104): the chart library's internal canvases have explicit `z-index:1`/`z-index:2`, while the component's own fallback hint (`EmptyHint`, for the "no candle series" case) sits in a sibling `position:absolute` div with `z-index:auto`, which CSS stacking rules always paint underneath the canvases — so the hint is present in the DOM but permanently invisible whenever this exact combination occurs. Separately, with zero bars the price axis never autoranges, so the `createPriceLine` calls for the 3 real levels have no visible position to draw at either.
  - **User impact:** a user who picks a symbol/as-of combination where levels exist but the representative bar series has no candles as-of that instant (a state the spec explicitly anticipates and requires a screenshot for) sees an unexplained blank panel with no error, no data, and no indication of why — the exact "silent failure" the phase's own critical anti-goal was written to prevent.
  - **Why this drives FAIL rather than WARN:** this is not a discoverability gap (the path to the state is fine) — it is one of the DoD's five explicitly required, screenshot-verified acceptance states, tied to a critical (not advisory) anti-goal, and the missing content is **completely inaccessible** (0-pixel match, confirmed twice by QA and once more by me) rather than merely hard to find. That meets this review's own FAIL bar ("feature is effectively inaccessible") rather than the WARN bar ("gap but not blocking").
  - Evidence: `reports/qa/goal-structure_ui-iter-1-evidence/UT-10-no-zones.png`, `UT-10-no-zones-recheck.png`; contrasted against `UT-06-populated-chart.png`.

### Visual Consistency
- The new `/structure` page matches the established dark instrument-panel style closely. Direct comparison of `apps/frontend/app/structure/page.tsx` against `apps/frontend/app/performance/page.tsx`: identical `max-w-7xl` single-column layout, the same slate surface/border tokens (`bg-slate-900/40`, `border-slate-800`), the same amber degraded/empty-state treatment (`border-amber-800/60 bg-amber-900/20 text-amber-300`), and `font-mono` for numeric cells.
- The zone class badge (`inline-block rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 ... text-slate-300`) is nearly identical to the badge markup already used on `/performance/page.tsx` (`rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[10px] text-slate-400`, confirmed by reading both files) — no new arbitrary color or invented badge style was introduced for A/B/C.
- The new chart's dark theme options (`background:#020617`, grid `#1e293b`, text `#94a3b8`, candle colors `#34d399`/`#fb7185`) are byte-identical hex values to `PriceChart.tsx`'s own chart options — confirmed by reading both files side by side. No visual drift between the two charts.
- No arbitrary/off-token values were found in the new page or chart component.

## Recommendation

1. **Before this iteration is considered done, fix the UT-10 blank-chart defect** in `apps/frontend/components/StructureChart.tsx`: give the `EmptyHint` overlay wrapper an explicit `z-index` higher than the chart library's internal canvases (e.g. `z-index: 10` or equivalent), and ensure the price axis has a usable range to draw the declared level lines against even when zero candles are present (or explicitly suppress the price lines and rely solely on a now-visible hint — either honestly satisfies the anti-goal, but one of the two must actually be visible).
2. **Recommend (non-blocking for this iteration, but should not be silently dropped):** check whether `apps/frontend/components/PriceChart.tsx`'s own `"Loading price history…"` / `"No price history for this window yet"` hint is subject to the same occlusion during the Cockpit's connecting/empty window, since it shares the identical markup pattern. If so, fix both components consistently (ideally via one shared chart-empty-state wrapper) rather than patching `StructureChart.tsx` alone.
3. No changes needed to nav discoverability, regression safety, or visual consistency — all three are solid in this iteration.
