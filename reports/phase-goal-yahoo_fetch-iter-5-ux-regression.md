# Phase goal-yahoo_fetch-iter-5 — UX Regression Review

**Date:** 2026-07-10

**Verdict:** UX-REGRESSION-WARN

## New Capability Discoverability

| Capability | Navigation path | Clicks from home | Label clarity | Visual feedback |
|---|---|---|---|---|
| "Fetch from Yahoo Finance" control (symbol + timeframe + start/end + button) | Top nav bar → **Structure** (`/structure`, `nav: true` in `apps/backend/app/meta.py:30`, unchanged this iteration) | 1 | Clear — panel titled "Fetch from Yahoo Finance", button reads the same | Button disables/re-labels to "Fetching…" while in flight; screenshots `TC-06-button-enabled.png` confirm disabled→enabled transition |
| "Yahoo Finance" provenance badge | Renders automatically beside the chart on any successful load (fetch or the pre-existing manual "Load") | 1 (same page) | Clear — small "feed" + value pill, same pattern as the cockpit's existing badge | Honestly absent when idle / no series charted (`if (!dataFeed) return null` in `FeedBasisBadge.tsx:55`) |
| Fetch-error honest states (422/503/504/409) | Renders inline below the fetch form via `UnavailablePanel` (`data-testid="fetch-yahoo-error"`) | 0 (same panel) | Distinct backend `detail` string per code, not generic | Amber degraded treatment, consistent with the rest of the page |

`/structure` was already registered with `nav: true` before this iteration (confirmed in `apps/backend/app/meta.py` and unchanged in this iteration's diff), and `NavBar.tsx` was not touched — so the new control inherits the page's existing 1-click reachability with zero additional navigation work needed. This part is clean: **PASS**.

## Regression Risk

| Shared component | Prior feature it served | This iteration's change | Risk |
|---|---|---|---|
| `FeedBasisBadge.tsx` | Cockpit live-feed basis stamp (J-67, built in `goal-i_will_be_super_rich_with_my_loved_ones` iter-24; single touch since) | `dataFeed` prop widened `"sim"\|"iex"\|"sip"\|null\|undefined` → `string\|null\|undefined`; render logic and the `if (!dataFeed) return null` guard are byte-identical (confirmed via `git diff`) | **Low** — type-only change, no behavior difference on `/` |
| `apps/frontend/app/structure/page.tsx` Registry / Comparison sections | J-02 registry+champion, J-03 backtest comparison (built in `goal-structure_ui` iter-1/2/3) | Not touched by this diff (confirmed via `git diff` — only header copy, new fetch section, new state, and the badge insertion point changed) | **Low** |
| `apps/frontend/lib/api.ts`, `lib/types.ts` | Every existing page that imports from these modules | Purely additive (`recordBarSeries()`, `RecordBarSeriesResult`); no existing export modified (confirmed via `git diff`) | **Low** |
| `apps/frontend/components/SymbolSearch.tsx` (via the pre-existing "Load" form's `symbolInput`) | J-04 manual Load flow (`goal-structure_ui` era) | **Not directly edited**, but newly exercised in a way it wasn't before: `handleFetchYahoo()`'s success path calls `setSymbolInput(result.bar_series.symbol)` on the Load form's own state. `SymbolSearch`'s `useEffect(() => {...}, [value])` (lines 44-68) re-fires on **any** value change — programmatic or typed — and ends with `setOpen(true)`, auto-opening the suggestions dropdown | **Medium — see Flags below, confirmed in evidence** |

## UI vs Backend Parity

| Backend capability | UI exposure | Assessment |
|---|---|---|
| `taxonomy.FEED_BASIS_LABELS["yahoo"] = "Yahoo Finance"` | Read verbatim by `FeedBasisBadge` via `GET /research/taxonomy` | Fully surfaced |
| `POST /research/bars` fetch/store-first (already backend-complete since earlier iterations) | Now triggerable via the new fetch control | Fully surfaced — this is the iteration's entire point |
| B2 fix — blank `?symbol=`/`?timeframe=` now normalizes to `None` before the no-param short-circuit | No UI control anywhere sends a blank symbol/timeframe value | Correctly classified backend-only; this is a defensive correctness guard for future/external callers, not a withheld feature — no gap |
| Live cache-miss Yahoo network fetch (as opposed to store-first serve) | Same UI control triggers it for a genuinely new window; **not exercised in this iteration's browser evidence** (explicitly integration-gated per spec) | Acceptable per spec's own scoping (`TAPEOLOGY_LIVE_INTEGRATION=1` only) — not a UI-exposure gap, but see the evidence-coverage flag below for a related, in-scope honest-state gap |

No backend capability is silently withheld from the UI. This part is clean: **PASS**.

## Flags

### Hidden Capabilities
- None. `/structure` was already navigable and no new page/route was added that lacks a path.

### Undiscoverable Capabilities
- None within 2 clicks. One soft usability note (not a flag-worthy defect): the new "Fetch from Yahoo Finance" panel sits directly above the pre-existing "Load" form, and both show a field labeled "Symbol" a few pixels apart (visible in `TC-05-fetch-control.png`). The page's reworded framing caption ("One explicit write action... everything else... is read-only") is a reasonable disambiguator, but a first-time user could plausibly wonder why there are two adjacent symbol boxes. Not blocking — no action required, just worth a look in a future polish pass.

### Potential Regressions
- **`SymbolSearch` dropdown auto-opens over the newly-loaded chart/badge after every successful fetch — confirmed in code and in the QA evidence itself.** `handleFetchYahoo()` seeds the pre-existing Load form's `symbolInput` state on success (`apps/frontend/app/structure/page.tsx`, `handleFetchYahoo`). That state feeds a `SymbolSearch` instance whose `useEffect(() => {...}, [value])` (`apps/frontend/components/SymbolSearch.tsx:44-68`) does not distinguish a user keystroke from a programmatic value change — it debounces, looks up suggestions, and calls `setOpen(true)` regardless. Result: **every** successful fetch, for **every** user, pops the Load form's suggestion dropdown open on top of the panel. This is directly visible in the QA agent's own screenshots `TC-07-chart-rendered.png` and `TC-08-levels-zones.png` — both show the "AAPL / AAPB / AAPD…" suggestion list open and overlapping exactly the region where the provenance badge renders (immediately above `<StructureChart>`) and the top rows of the level-price list to the right of the chart. The dropdown self-dismisses on an outside click and no data is lost or corrupted, so this does not block the journey — but it means the primary "proof" screenshots for this era's headline moment (candles + level lines + provenance badge, per the DoD) do not, in fact, clearly show the badge or the full level list without an extra click first. This was disclosed informally by the developer as a "cosmetic" Known Issue in both `docs/handoffs/goal-yahoo_fetch-iter-5-dev.md` and `-frontend.md`, but it was not raised as a structured finding by either the reviewer or QA report, and it does visibly appear, unremarked-on, in QA's own attached evidence. Recommend the fix the frontend handoff itself already suggests: don't re-fire `SymbolSearch`'s suggestion effect on a programmatic value change (e.g., gate on a user-interaction flag, or expose a variant of `onPick`-style silent-set that skips the lookup).
- **J-04 (manual Load form) and J-06 (`/`, `/journal`, `/studies`, `/performance`) regression checks**: code-verified low risk (see table above) and QA's prose asserts both spot-checks passed, but neither is broken out as its own itemized, evidenced test case in the QA report's structured 15-item table (they appear only as narrative bullets). Not a defect — just weaker evidentiary rigor than the rest of the report's per-TC structure.

### Visual Consistency
- New panel correctly reuses `Panel`, `INPUT_CLASS`, and the same button classes (`border-slate-600 bg-slate-800`, active/disabled states) as the existing Load/Run-comparison controls — confirmed via diff and screenshot; no arbitrary styling or new visual effects introduced. No deviation from the established dark instrument-panel design system.
- The one visual-consistency defect is the dropdown-overlap issue described above under Potential Regressions — it is a z-index/interaction-ordering artifact, not a token/style deviation.

### Evidence Gap Against an Explicit DoD Item (new finding)
- The phase's own Definition of Done requires: *"A symbol with no stored bars renders the distinct honest empty state (browser or unit)."* The QA agent's own test plan (`reports/qa/goal-yahoo_fetch-iter-5-test-plan.md`) planned this as **TC-11 — Empty state when no bars stored for symbol** (browser test). **TC-11 does not appear anywhere in the executed QA report** (`reports/qa/goal-yahoo_fetch-iter-5-qa.md`) — not as pass, fail, or explicitly skipped; the report's own tally ("15/15 executed and passed") excludes it entirely, and no screenshot or narrative mention covers it. Code inspection shows the underlying mechanism (`levels.no_bar_series_for_symbol` → `structure-no-bar-series` testid, `apps/frontend/app/structure/page.tsx:1066-1068`) is unmodified by this iteration's diff, so there is no evidence of breakage — but there is also no evidence this iteration that the honest empty state actually renders end-to-end for the new fetch-driven flow, despite it being a named, checkbox-level DoD requirement and an explicitly-designed browser test case in the ui-surface-map. This is a coverage gap, not a confirmed defect.

## Recommendation

1. **(Should-fix, low effort)** Stop `SymbolSearch`'s suggestion dropdown from auto-opening when its `value` changes programmatically (i.e., from `handleFetchYahoo`'s `setSymbolInput` call) rather than from a user keystroke — e.g., skip the lookup/`setOpen(true)` when the value was set via a non-typing path, or debounce off a "dirty by typing" flag instead of raw `value`. This directly affects the visual clarity of the era's headline "fetch-from-the-app" moment.
2. **(Should-verify)** Re-run or explicitly record TC-11 (a symbol/window with no data resulting in the honest empty state through the new fetch control) before treating J-05's honest-states requirement as closed with browser evidence — today it is only supported by static code reading, not a browser run.
3. No action required on discoverability, navigation, or UI/backend parity — all clean.

Neither finding blocks the underlying capability or constitutes a broken prior journey (hence WARN, not FAIL): the fetch control works, the badge is data-driven and correctly absent when idle, and no prior page's functionality regressed. Both items are concrete, evidenced gaps a future pass should close.
