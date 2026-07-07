# Phase goal-structure_ui-iter-2 — UI Surface Map

**Phase:** goal-structure_ui-iter-2
**Date:** 2026-07-07
**Written by:** ui-impact-analyst

---

## Code Change Classification

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/frontend/app/structure/page.tsx` | frontend-direct | direct | +299/-12 lines. Adds the new Registry section (2 strategy cards, champion badge, cross-check caption, loading/unavailable states) below the existing Levels & Zones section. This is where every user-visible change in this iteration actually renders. |
| `apps/frontend/lib/types.ts` | frontend-direct (supporting/data layer) | indirect — enables | +51 lines. Adds `Strategy`, `StrategyExits`, `StrategyExitRule`, `StrategiesPayload` interfaces consumed by `page.tsx`. No standalone UI surface of its own — a type definition is not something a user can navigate to or click. |
| `apps/frontend/lib/api.ts` | frontend-direct (supporting/data layer) | indirect — enables | +23 lines. Adds `fetchStrategies()`, the fetch wrapper for `GET /research/strategies`, mirroring the existing `fetchProfiles()`. No standalone UI surface — consumed only by `page.tsx`'s mount-time effect. |
| `apps/frontend/components/StructureChart.tsx` | frontend-direct | direct, but **byte-unchanged this iteration** | No diff. Confirmed by direct read that the prior iteration's empty-state fix (line 99 `z-10`, line 100 "No candles to draw at this as-of time.") is already present. This iteration's scope was independent re-verification of that existing fix (J-01 closure), not new code — flagged here because the phase spec explicitly requires a fresh browser check of this surface. |
| `apps/backend/app/research/strategies.py`, `profiles.py`, `routes.py`, `meta.py`, `config.py` | — | none | Zero backend diff this iteration (`git diff --stat -- apps/backend/` is empty). `GET /research/strategies` and `GET /research/profiles` already existed pre-iteration; the new frontend code is their first browser consumer. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/structure` | Registry section container (`<section aria-label="Strategy registry">`, `Panel title="Registry"`) | New section | J-02: makes the strategy registry + champion visible in-app for the first time, below the existing Confluence-zones section | Navigate to `/structure` with the symbol and as-of fields left empty (do not click Load); confirm a "Registry" panel appears below the "Confluence zones" section without any click, containing the read-only disclaimer text, a Champion panel, and two strategy cards. |
| `/structure` | Strategy card — `v1` (`data-testid="strategy-card"`, `data-strategy-id="v1"`) | New component | J-02: surfaces `v1`'s config-owned entry/exit rules verbatim from `GET /research/strategies` | On the Registry section, find the card where `data-strategy-id="v1"`; confirm it shows entry rule `state_native_sustained_premise`, `r_stop` = `synthetic_invalidation_at_arm`, `state_flip` = `opposing_control_state`, `horizon (seconds)` = `120`, `dataset_end` = `forced_exit_at_last_recorded_price`, and that **no** `reward_target` row is rendered on this card; cross-check every value against `GET /research/strategies` (e.g. the `mcp__tapeology__strategies` tool or `curl <backend>/research/strategies`). |
| `/structure` | Strategy card — `structure_tape` (`data-testid="strategy-card"`, `data-strategy-id="structure_tape"`) | New component | J-02: surfaces `structure_tape`'s config-owned entry/exit rules plus its class-scaled maps, verbatim | On the Registry section, find the card where `data-strategy-id="structure_tape"`; confirm it shows all of `v1`'s field types PLUS a `reward_target` row (`class_r_multiple_bounded_by_next_opposing_level`) and three tables — "stop (bps by class)" (A=1, B=5, C=10), "reward target (R-multiple by class)" (A=3, B=2, C=1), "size (multiple by class)" (A=2, B=1, C=0.5); cross-check every value against `GET /research/strategies`. |
| `/structure` | Champion panel (`data-testid="champion-summary"`, `champion-strategy`, `champion-profile`) | New component | J-02: surfaces the frozen champion pointer in-app for the first time (previously only visible on `/performance` or via API/MCP) | On the Registry section, read the `champion-strategy` and `champion-profile` values; confirm they show `v1` and `default`; independently fetch `GET /research/profiles` and confirm its `champion.strategy_id`/`champion.profile` match these two values byte-for-byte. |
| `/structure` | Champion cross-check caption (`structure-champion-crosscheck-pending` / `-unavailable` / `-match` / `-mismatch`) | New component (honest-state narration) | J-02 DoD requirement: the champion shown must be confirmed to equal `GET /research/profiles`'s champion, not just assumed | Reload `/structure` and wait for both fetches to resolve; confirm the caption directly below the Champion panel's fields carries `data-testid="structure-champion-crosscheck-match"` and reads "Confirmed identical to the champion served by GET /research/profiles — one store pointer, two read views." (The `-pending`/`-unavailable`/`-mismatch` variants are not reachable in this environment — see Known Limitation below; do not fail this check for their absence.) |
| `/structure` | Registry-unavailable panel (`data-testid="structure-registry-unavailable"`) | New honest state | J-02 DoD requirement: no fabricated registry/champion when the backend is unreachable | Stop only the backend process (leave the frontend running) and reload `/structure`; confirm the Registry section's location now shows an amber panel with `data-testid="structure-registry-unavailable"` reading "Backend unreachable — is the API running?", and that no strategy cards or Champion panel render anywhere on the page. Restart the backend and reload to confirm the section repopulates. |
| `/structure` | Registry-loading panel (`data-testid="structure-registry-loading"`) | New transient state | Shown while `GET /research/strategies` / `GET /research/profiles` are in flight on mount | Using browser devtools network throttling (e.g. "Slow 4G"), hard-reload `/structure`; confirm a pulse-skeleton placeholder with `data-testid="structure-registry-loading"` is visible briefly in the Registry section's location before the populated cards/panel appear. |
| `/structure` vs `/performance` | Reused testid strings (`champion-summary`, `champion-strategy`, `champion-profile`) | Regression check (no code change on `/performance`) | The new `/structure` Champion panel deliberately reuses `/performance`'s exact champion-badge testid strings; since the two routes render different components, a naive test suite could otherwise cross-match the wrong element | Load `/performance` directly (not by navigating from `/structure`) and confirm its own pre-existing champion summary block still renders its correct values with no visual or functional interference from the identically-named testids used on `/structure`. |
| `/structure` | Price-chart empty-state overlay (`StructureChart.tsx`'s `!hasBars` hint, "No candles to draw at this as-of time.") | Re-verified existing (J-01 closure) — **no code change this iteration** | The prior iteration's fix for this silent-blank-chart defect is confirmed present in the code, but per project lessons an in-tree fix isn't "done" until independently re-verified live | Enter a symbol/as-of combination that yields levels but no recorded bars (or any as-of before/after available bar coverage), click Load; confirm the chart canvas area shows the fully-visible text "No candles to draw at this as-of time." (not a blank/black box, and not text hidden behind the chart canvas). |
| `/structure` | Existing Levels & Zones section (price chart + confluence-zones table) | Regression check (no code change) | Confirms the new Registry section addition introduces no layout/functional regression to the pre-existing section above it | Enter a symbol/as-of combination known to have recorded bars, levels, and at least one confluence zone, click Load; confirm the chart, dashed level lines, and the A/B/C-badged confluence-zones table render exactly as before, and that scrolling to the new Registry section below causes no visual overlap or state interference with this section. |

<!-- Change Type used above beyond the template's suggested list: "New honest state", "New transient state", "Regression check (no code change)", "Re-verified existing (no code change)" — used where "New component"/"Changed behavior" would misrepresent whether new code was written. -->

---

## Backend-Only Changes (No UI Impact)

None. This iteration made zero backend edits (`git diff --stat -- apps/backend/` is empty). `GET /research/strategies` and `GET /research/profiles` already existed prior to this iteration and are unchanged — they are simply read by the new frontend code for the first time.

---

## Summary

- **Frontend surfaces changed:** 1 (`/structure` route; no other route touched)
- **New pages/routes:** 0 (Registry section appended to the existing `/structure` page; no new route, no new nav entry)
- **Modified components:** 1 file modified (`apps/frontend/app/structure/page.tsx`), introducing 2 new sub-components (`StrategyCard`, `ClassMapTable`) and 1 new helper (`championsMatch`); reuses existing `Panel`, `LoadingPanel`, `UnavailablePanel` without redefining them
- **Supporting (non-surface) files changed:** 2 (`apps/frontend/lib/types.ts`, `apps/frontend/lib/api.ts`) — enable the above but have no independent user-facing surface of their own
- **Re-verified (no code change) surfaces:** 1 (`apps/frontend/components/StructureChart.tsx`'s empty-state overlay — J-01 closure target)
- **Navigation changes:** no
- **Backend-only changes:** 0
