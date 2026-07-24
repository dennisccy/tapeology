# Phase goal-clean_slate-iter-2 — UI Surface Map

**Phase:** goal-clean_slate-iter-2 (J-02: "Frontend + WS demolition — the two-page product")
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| Every kept page (`/`, `/structure`) | `NavBar` (top navigation bar) | Removed navigation | `app/meta.py`'s `UI_ROUTES` tuple trimmed from 6 rows to 2 (the `/journal`, `/journal/[id]`, `/studies`, `/performance` rows deleted). `NavBar.tsx` itself is byte-unedited — it renders `GET /meta/ui-routes` verbatim with no hardcoded fallback list, so it shrinks automatically. | Load `/`, then load `/structure`. On each, confirm the top nav shows exactly two links, labeled "Cockpit" and "Structure", and that no "Journal", "Studies", or "Performance" link appears anywhere. |
| `/journal` | Page deleted (was `JournalTable`, `JournalFilterBar`, `HintLog`) | Removed element | `apps/frontend/app/journal/page.tsx` deleted along with its 3 supporting components; the manual trade-journal list + hint-activity log no longer exists. | Navigate directly to `/journal`. Confirm it renders the app's existing dark-styled "not found" page — not a blank screen, not a redirect, not a 500 error. |
| `/journal/[id]` | Page deleted (was `JournalDetailView`) | Removed element | `apps/frontend/app/journal/[id]/page.tsx` deleted along with its detail-view component. | Navigate to `/journal/1` (any id value). Confirm it renders the same "not found" page as `/journal`, not a crash or a blank detail shell. |
| `/studies` | Page deleted (was `StudyList`, `StudyCreateForm`, `StudyResultsView`) | Removed element | `apps/frontend/app/studies/page.tsx` deleted along with its 3 supporting components; the replay-studies workbench no longer exists. | Navigate to `/studies`. Confirm the "not found" page renders and there is no "Create Study" form or study-results list anywhere on screen. |
| `/performance` | Page deleted (was `AnalyticsView`) | Removed element | `apps/frontend/app/performance/page.tsx` deleted along with its analytics component. | Navigate to `/performance`. Confirm the "not found" page renders and no analytics charts or tables appear. |
| `/` (Cockpit) | `ThesisStrip` (deleted; previously rendered between the price chart and the panel grid, in both a "live" and a post-Stop "surviving thesis" variant) | Removed element | The manual thesis declare/resolve/track workflow was deleted along with the backend WS `thesis` projection that fed it. | Click "Watch" for `SIM-BUYER`, wait for the tape state to reach `buyer_control`, then click Stop. Confirm no thesis strip (no "Declare thesis" line, no verdict/stance/grade text) renders anywhere between the chart and the panel grid at any point in the flow — during the watch or after Stop. |
| `/` (Cockpit) | `HintDock` (deleted; previously rendered directly under `TapeStatePanel`) | Removed element | The setup-forming hint declare affordance was deleted along with the backend WS `hint` projection that fed it, and the now-dead `onHintDeclare` prop was removed from `Cockpit.tsx`'s own signature. | During the same `SIM-BUYER` watch used above, confirm no hint panel or "declare from hint" button renders under the Tape State panel. |
| `/` (Cockpit) | `SoundCue` (deleted; its only render site was nested inside `ThesisStrip`) | Removed element | Deleted along with its sole parent, `ThesisStrip`. | During the same watch, confirm no mute/sound-toggle icon or control is visible anywhere on the cockpit screen. |
| `/` (Cockpit) | `PriceChart` — thesis-geometry overlay only | Changed behavior | `PriceChart.tsx`'s thesis-derived marker and price-line construction (the `thesisSpecs` memo half, `VERDICT_COLORS`/`PRICE_LINE_COLORS`/`MARK_COLOR`) was removed. Tape-state markers, candle rendering, timeframe switching, the S/R band overlay, and live bar movement were not touched. | Watch a ticker (e.g. `SIM-BUYER`, or a real AAPL Historical replay). Confirm candles render, the Tape/History timeframe selector switches views, the S/R band overlay renders (visible on a real AAPL 1h History view), and live bars keep moving as new trades arrive — and confirm no circle or up-arrow thesis markers, and no dashed invalidation/level price lines, are drawn on the chart. |
| `/` (Cockpit) | `app/page.tsx` — Stop flow | Changed behavior | The post-Stop "surviving thesis" branch (`survivingThesis` state plus its `GET /research/thesis/active` read inside `handleStop`) was deleted; Stop now always falls through to the plain idle/failure branches. | Watch `SIM-BUYER`, let it settle into any tape state, then click Stop. Confirm the screen returns directly to the plain "No ticker watched" idle screen — no intermediate "surviving thesis" panel appears, regardless of the tape state at the moment Stop was clicked. |
| N/A — WebSocket payload (`/tape/{ticker}/stream`) | WS frame JSON | Changed behavior (fields removed) | `app/main.py` no longer merges `frame["thesis"]` / `frame["hint"]` into the outgoing frame (both merge lines and their two helper functions, `_thesis_projection`/`_hint_projection`, were deleted); the frame is now the engine projection only. | While watching `SIM-BUYER`, open browser devtools → Network → WS (or run `websocat ws://localhost:<port>/tape/SIM-BUYER/stream`), inspect one frame's JSON, and confirm it has no `thesis` key and no `hint` key, while `ticker`, `stream_status`, `tape_state`, `features`, `recent_trades`, and the other pre-existing keys are still present. |
| `/structure` | `StructureChart` + Load flow | Changed behavior — regression check, not edited this iteration | `StructureChart.tsx` has zero diff this iteration (verified via `git diff`), but it is re-verified because it is the same renderer `PriceChart.tsx` delegates to, and `PriceChart.tsx` was edited. | Load `/structure`, select the pinned AAPL as-of date, and click Load. Confirm the chart renders the same 300–302.4-class resistance wall band (Class A, score 171, 849 members, round number) as before this iteration. |
| `/` (Cockpit, any watch) | `FeedBasisBadge` (rendered inside `TopBar`) | Changed behavior — regression check, not edited this iteration | Neither `FeedBasisBadge.tsx` nor `TopBar.tsx` was touched; re-verified because the badge depends on `GET /research/taxonomy`, which sits adjacent to this iteration's WS/nav changes. | Watch `SIM-BUYER` and confirm the feed-basis badge shows "Simulated". Separately, watch a real historical AAPL replay and confirm the badge shows "SIP (consolidated)" — two different served labels, proving the badge still reads live data rather than a hardcoded string. |

**Note on non-visual supporting files:** `apps/frontend/lib/api.ts` (14 fetch functions deleted)
and `apps/frontend/lib/types.ts` (~30 types deleted, `ResearchTaxonomy` slimmed, `thesis`/`hint`
dropped from `TapeSnapshot`) render nothing themselves — they are the fetch/type layer the
deleted pages and components above called into. Their changes are fully absorbed into the rows
above; they have no independent UI surface of their own. The only directly verifiable check
specific to these two files is a clean TypeScript build: run `npx tsc --noEmit` in
`apps/frontend` and confirm zero type errors (this would fail immediately if any deleted
page/component still referenced a removed function or type).

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/routes.py` — deleted `ResearchRegistry`'s `_monitors` dict and the
  `monitor_for`/`projection_for`/`_surviving_projection`/`hint_projection_for` methods. These were
  already permanent, always-`None`-returning stubs before this change (kept alive only because
  `app/main.py`'s WS merge — removed in this same iteration — still called them); their removal is
  pure code hygiene with no behavioral or UI effect, before or after.
- `apps/backend/tests/test_meta_routes.py` — two tests rewritten to assert the 2-route payload,
  two tests deleted, two left unchanged. Test-only file; no UI surface affected.
- `apps/backend/tests/test_profile_equivalence.py` — one test deleted (it read the now-deleted
  `/performance` page's source file directly off disk to assert a UI constraint on a page this
  iteration removes). Test-only file; no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 13 rows (11 actually changed; 2 re-verified unchanged as
  regression checks — `/structure` and the feed-basis badge)
- **New pages/routes:** 0
- **Removed pages/routes:** 4 (`/journal`, `/journal/[id]`, `/studies`, `/performance`)
- **Modified components (edited in place):** 3 (`app/page.tsx`, `Cockpit.tsx`, `PriceChart.tsx`)
- **Removed components:** 11 (`JournalTable`, `JournalDetailView`, `JournalFilterBar`,
  `ThesisStrip`, `HintDock`, `HintLog`, `SoundCue`, `StudyList`, `StudyCreateForm`,
  `StudyResultsView`, `AnalyticsView`)
- **Navigation changes:** yes — top nav shrinks from 5 links to 2
- **Backend-only changes:** 3 (`app/research/routes.py`, `test_meta_routes.py`,
  `test_profile_equivalence.py`)
