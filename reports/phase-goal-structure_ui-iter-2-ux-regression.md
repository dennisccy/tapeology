# Phase goal-structure_ui-iter-2 — UX Regression Review

**Date:** 2026-07-07

**Verdict:** UX-REGRESSION-PASS

<!-- New capability (J-02 Registry + champion) is fully discoverable at 0 additional clicks past
     the existing 1-click nav entry, confirmed by both browser-qa-agent evidence and my own direct
     read of page.tsx. Iter-1's genuine UX-REGRESSION-FAIL (the J-01 silent-blank-chart defect) is
     independently re-verified this iteration and closed — computed-style evidence confirms the fix
     holds. No confirmed regression to any prior journey; diff to shared files is additive-only,
     verified at the source level, not just from reports. One non-blocking copy/orientation gap is
     documented under Recommendation. -->

## New Capability Discoverability

| New capability | Navigation path | Clicks from home | Verdict |
|---|---|---|---|
| `/structure` page itself | Top-bar "Structure" link (unchanged since iter-1; data-driven from `GET /meta/ui-routes`, confirmed byte-unchanged this iteration via `git status`) | 1 | Discoverable |
| **Registry section** (2 strategy cards) | Same `/structure` page, renders automatically on mount via a `useEffect` independent of the Levels & Zones Load button (confirmed by direct read of `page.tsx`'s `strategiesResult`/`profilesResult` state + effect) | 0 additional (scroll only, no click) | Discoverable — confirmed live by browser-qa-agent UT-01/UT-02 (Registry populates before any form interaction) and UT-14 (visible after one scroll, no second click) |
| **Champion badge** | Top of the same Registry section | 0 additional | Discoverable — UT-05 confirms `champion-strategy`/`champion-profile` render and cross-check against `GET /research/profiles` |
| **Registry-unavailable honest state** | Same section location, replaces the cards when `GET /research/strategies` is unreachable | 0 additional | Discoverable — UT-08 confirms the amber panel with distinct `data-testid="structure-registry-unavailable"` and no fabricated fallback |
| **J-01 closure** (levels-but-no-candles honest hint) | Same page, appears in the chart panel after Load with a qualifying as-of | 1 (Load click) | Discoverable — UT-06 independently re-verified live this iteration (see Regression Risk) |

The nav entry itself is unchanged from iter-1 (verified: `apps/frontend/components/NavBar.tsx` is not in this iteration's changed-files list, and I read it directly — it remains fully data-driven off `GET /meta/ui-routes` with zero hardcoded routes). No new route, no new nav entry was needed or added, matching the phase spec's own "Navigation changes: none."

**One discoverability observation, not rising to a flag:** I read the page's header (`page.tsx:462-474`) directly. The `<h1>` ("Structure") and its subtitle ("Deterministic support/resistance levels and A/B/C confluence zones for a chosen symbol and as-of time.") were **not updated this iteration** to mention the new Registry/strategy-registry/champion content — they still describe only the J-01 Levels & Zones capability. For comparison, I read `/performance/page.tsx:219-230` directly: its own subtitle explicitly summarizes **both** of that page's major sections ("one append-only PnL-ledger row per enhancement... beside the current champion") — i.e., this codebase's own established precedent is for a page's subtitle to preview everything below it, and `/structure`'s subtitle now undershoots that precedent by one section. This matters slightly more than a typical copy nit because, per `user-visible-changes.md`'s own "Data reality" note, in this keyless environment the Registry section is the *only* content populated by default (Levels & Zones stays idle until a symbol/as-of with recorded bars is supplied) — so a first-time visitor who reads the subtitle, sees the idle Levels & Zones panel, and takes the subtitle at face value has no on-page textual cue that anything else exists below. This does **not** meet this review's discoverability-flag bar (the skill's own click-based test rates 0-additional-click, scroll-only content as discoverable, and browser QA independently confirms real visibility with no interaction), so it is not flagged as hidden/undiscoverable — it is called out here as a specific, evidenced, non-blocking recommendation instead (see Recommendation).

## Regression Risk

Per the UI Regression Scout method, cross-referencing this iteration's changed files (`git diff --stat -- apps/` = `page.tsx` +299/-12, `api.ts` +23/-0, `types.ts` +51/-0 — confirmed directly, not just cited from reports) against components load-bearing for prior journeys:

| Shared component | Prior feature it serves | This iteration's touch | Risk |
|---|---|---|---|
| `apps/frontend/app/structure/page.tsx` | J-01 (Levels & Zones, iter-1) | Read the full diff directly: the entire J-01 JSX block (controls, four honest states, chart panel, zones panel) is untouched except for the header doc-comment; the new Registry `<section>` is appended immediately after the existing section's closing tag. New `useEffect`/state hooks are additive (new `strategiesResult`/`profilesResult`, no existing state touched) | Low — confirmed by source read AND by fresh browser-qa-agent re-test: UT-07 (populated chart+zones render unchanged alongside the new section, no layout break), UT-09/UT-10/UT-11 (all three no-bar-series / no-levels / malformed-`as_of` honest states re-verified byte-identical) |
| `apps/frontend/lib/api.ts` | Every page's data fetching (`fetchLevels`, `fetchProfiles`, etc.) | Purely additive — `git diff --stat` shows `+23/-0`; `fetchStrategies()` is a new export beside the untouched `fetchProfiles()` | None |
| `apps/frontend/lib/types.ts` | Every page's type contracts | Purely additive — `+51/-0`; new `Strategy`/`StrategyExits`/`StrategyExitRule`/`StrategiesPayload` interfaces only, `StrategiesPayload.champion` reuses `ProfilesPayload["champion"]` rather than declaring a second shape (confirmed by direct read) | None |
| `apps/frontend/components/NavBar.tsx` | Site-wide nav (all prior journeys) | Not in the changed-files list; read directly — still 100% data-driven off `GET /meta/ui-routes`, zero hardcoded routes | None |
| `apps/frontend/components/StructureChart.tsx` | J-01's chart | Not in the changed-files list this iteration. **This is the critical carry-over item from iter-1's UX-REGRESSION-FAIL.** I read the file directly: line 99 still carries `z-10` on the `!hasBars` overlay, line 100 still reads "No candles to draw at this as-of time." — the iter-1 audit's fix is intact. Browser-qa-agent additionally re-verified this **live**, independent of the code read: UT-06 used `getComputedStyle` to confirm the hint wrapper computes `z-index:10` against the `lightweight-charts` canvases' `z-index:1`/`2` — the fix demonstrably holds in the running app, not just in the source | **Closed.** This satisfies the exact process gap lessons.md iter-1(b) called out (an in-tree fix isn't "done" until browser-QA re-runs independently and the records reconcile) |
| `champion-summary`/`champion-strategy`/`champion-profile` `data-testid` strings | `/performance`'s pre-existing champion box | The new `/structure` Registry section deliberately reuses these exact strings (confirmed by direct read of both files) | None functionally — the two routes never render simultaneously, and UT-12 independently confirmed (via direct navigation, not a link click) that `/performance`'s own champion box, profile registry, and PnL ledger all render correctly and unaffected. Noted only as a minor future test-suite-hygiene item: an automated test that queries `data-testid` globally rather than scoped to a container could in principle cross-match — worth scoping test queries per-page, not a product defect |
| `apps/backend/*` (`meta.py`, `research/strategies.py`, `research/profiles.py`, `research/routes.py`, `config.py`) | All backend-served journeys | Zero diff — confirmed via `git diff --stat -- apps/backend/` (empty) | None — this iteration is frontend-only as planned |
| `/`, `/journal`, `/studies` | Cockpit, Journal, Studies journeys (prior sessions) | Not in the changed-files list at all | None |

No regression is observed or expected in any prior journey. This iteration's own regression testing was substantive, not superficial: it re-drove all four of J-01's honest states plus the populated state plus the previously-broken fifth state (levels-but-no-candles), and separately re-verified `/performance`'s champion box — a meaningfully thorough regression pass given the shared-file touch to `page.tsx`.

## UI vs Backend Parity

| Backend capability | Surfaced in UI this iteration? | Assessment |
|---|---|---|
| Strategy registry — entry rule, exit fields (`r_stop`, `reward_target` where defined, `state_flip`, `horizon_seconds`, `dataset_end`) | Yes — two strategy cards, verified byte-for-byte by browser QA (UT-03, UT-04) against a direct `curl` of `GET /research/strategies` | Full parity |
| `structure_tape`'s class-scaled maps (`stop_bps_by_class`, `r_multiple_by_class`, `size_multiple_by_class`) | Yes — three `ClassMapTable` instances on the `structure_tape` card only, verified byte-for-byte (UT-04) | Full parity |
| Champion pointer (`champion.strategy_id`/`champion.profile`) | Yes — badge + cross-check caption against `GET /research/profiles`, verified byte-for-byte (UT-05) | Full parity, single-source-of-truth confirmed live (not just asserted) |
| `Strategy.fees` / `Strategy.slippage` / `Strategy.dollars_per_r` (modeled in the new `types.ts` `Strategy` interface, mirroring the plan's own instruction to mirror the full served shape) | No — not rendered on either card (confirmed by direct read of `StrategyCard`'s JSX) | **Not a gap.** Neither `docs/goal.md`, the phase spec's "New information displayed" section, nor the DoD calls for these three fields to be displayed; the dev handoff's own "Design notes" section independently reasons through exactly this kind of minimal-field-set choice for `v1`'s unrendered `r_stop.spread_multiple`/`floor`. This is the same pattern iter-1's UX review already accepted for `SrLevel.touch_count`/`strength` (typed, not displayed, not in scope) — applying that same established, consistent standard here |
| Backtest comparison (`structure_tape` vs `v1`, J-03) | No | **Intentional, consistently documented deferral** — explicitly out of scope per the phase spec's OUT OF SCOPE section, the plan, and `user-visible-changes.md`'s "Not Visible Yet" section; targeted at a future iteration per the goal's J-01→J-02→J-03 order |
| Champion-pointer mutation / promotion path | No, and correctly so | This iteration's anti-goals explicitly forbid any `set_champion_pointer` call from the UI; confirmed absent by direct read — the Registry section is read-only (also independently confirmed by browser QA UT-15: zero interactive elements inside the Registry section) |

No parity gap is flagged. Backend made zero changes this iteration (`git diff --stat -- apps/backend/` is empty, confirmed directly) — both consumed endpoints (`GET /research/strategies`, `GET /research/profiles`) pre-existed; this iteration is genuinely just their first browser consumer, and it surfaces everything the phase actually scoped.

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None meeting this review's discoverability bar (0 additional clicks past the existing 1-click nav entry; confirmed live by browser QA, not just by code inspection). See the header-subtitle observation under "New Capability Discoverability" above and the Recommendation below — documented as a specific, evidenced, non-blocking polish item rather than a flag, since the capability is genuinely reachable and was independently confirmed reachable by browser-qa-agent.

### Potential Regressions
None confirmed. All touched shared files (`page.tsx`, `api.ts`, `types.ts`) are additive-only at the source level (verified directly, not only cited from reports); `NavBar.tsx` and `StructureChart.tsx` are byte-unchanged; `/performance`'s reused testid strings were independently re-verified live to cause no interference (UT-12). The one item that WAS a confirmed regression last iteration — the J-01 levels-but-no-candles silent blank chart (iter-1's own `UX-REGRESSION-FAIL`) — is independently re-verified this iteration via live `getComputedStyle` evidence (UT-06) and is now closed.

### Visual Consistency
- Confirmed by direct side-by-side source comparison (not just report citation): the Registry section's strategy-card shape (`rounded-lg border border-slate-800 bg-slate-900/60 p-4`, `page.tsx:229` in the new `StrategyCard` component) is byte-identical to `/performance/page.tsx`'s own `LedgerRowPanel` (`page.tsx:81`) and champion-summary block (`page.tsx:289`).
- `LoadingPanel` and `UnavailablePanel` are reused from this same file's existing local definitions (`page.tsx:100`, `:115`) rather than redefined — confirmed by direct read; no new visual language introduced for the loading/unavailable states.
- Amber unavailable-state tokens (`border-amber-800/60 bg-amber-900/20 text-amber-300`) and font-mono numeric convention (`NUMERIC_CELL`/`LABEL_CELL`) match the page's own pre-existing constants — no new color or typography scale introduced.
- Layout: single column inside the same `max-w-7xl` container as every other page in the app; no sidebar, no new grid, matching the plan's explicit visual requirement.
- No arbitrary/off-token values found anywhere in the new JSX (`StrategyCard`, `ClassMapTable`, the Champion box block).
- The one deviation from established page-level precedent is the header-subtitle completeness gap noted above (compared directly against `/performance/page.tsx`'s subtitle, which does summarize its full page content) — a copy-completeness issue, not a component-style or design-token deviation.

## Recommendation

1. **(Non-blocking, cosmetic)** Update `/structure`'s `<h1>` subtitle (`page.tsx:466-469`) and/or its `structure-framing` line (`:470-473`) to mention the Registry/strategy-registry-and-champion content, mirroring the precedent `/performance/page.tsx`'s own subtitle already sets by summarizing every major section of that page in one line. This is worth doing soon rather than "someday" because, in the current keyless environment, the Registry section is the only content populated by default on this page.
2. No other action required. J-02's new capability is fully discoverable and verbatim-parity with its backend source; no regression was found in any prior journey (extensively re-tested, not merely diffed); iter-1's genuine UX-REGRESSION-FAIL (J-01's silent blank chart) is independently re-verified live and closed this iteration; visual style is consistent with established design-system precedent.
