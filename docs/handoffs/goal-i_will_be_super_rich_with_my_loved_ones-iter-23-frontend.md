# goal-i_will_be_super_rich_with_my_loved_ones-iter-23 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-23 (J-65 — setup-forming hints)
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete

## What Was Built (UI)

Two new user-visible surfaces, both at their pre-registered blueprint homes — no new route, no nav change.

### 1. Hint dock on `/` (under the tape-state panel)
- `components/HintDock.tsx` (NEW) renders the served active hint VERBATIM: the pattern label, the plain-language evidence (with its measured sustain duration), the baseline citation (the user's studied baseline or exactly "no studied baseline — unvalidated pattern"), and the backend-owned "Descriptive only — not trading advice" register line.
- **Visible only when a hint is active** — the dock is absent (no empty-state chrome) on an idle/unclear tape. It reads the snapshot's additive `hint` key (pushed live over the WS); the frontend recomputes nothing.
- **Amber/neutral styling** per the design system (the absorption/unclear semantics), matching the existing risk-flag chip register (left accent rule + a subtle amber surface). Every interactive element has hover/focus/active states.
- **Declare affordance** prefills the thesis strip's declare form with the hint's setup + direction (via a `prefill` prop lifted to `app/page.tsx`); `invalidation_price` is left EMPTY and required — the user types it (one click never creates a thesis). On submit the form passes `declared_from_hint_id`. The affordance is **hidden while a thesis is already active** on the ticker (the no-dead-control pattern — no control that would only produce a 409).
- Placement: in `components/Cockpit.tsx`, the tape-state panel and the dock share one grid cell as a flex column, so the dock sits directly under the tape-state panel.

### 2. Hint log in `/journal` (third in-page view)
- The journal view switcher gains a "Hints" tab (theses | analytics | hints) — NO new route, NO nav change. `components/HintLog.tsx` (NEW) renders `GET /research/hints` rows verbatim, newest-first: time (via the one shared `dd-MM-yyyy` formatter), ticker, pattern, evidence, baseline citation, declared-from (a taxonomy-owned label badge once the user declared from the hint, else "—").
- Loading (pulsing-dot skeleton), error (styled rose alert), and honest empty states are all handled (empty-state copy from the taxonomy). Lazy-loaded on first switch to the view; refreshes on each re-open.

## Files Changed
- `apps/frontend/lib/types.ts` -- `Hint`, `HintsTaxonomy`, snapshot `hint` key, taxonomy `hints` block.
- `apps/frontend/lib/api.ts` -- `fetchActiveHint`, `fetchHints` (+ `HintsListResult`); `declared_from_hint_id` on `declareThesis`.
- `apps/frontend/components/HintDock.tsx` -- NEW.
- `apps/frontend/components/HintLog.tsx` -- NEW.
- `apps/frontend/components/Cockpit.tsx` -- renders the dock under the tape-state panel; threads `onHintDeclare`.
- `apps/frontend/components/ThesisStrip.tsx` -- `prefill` prop (`ThesisPrefill`) applied via an effect; `declared_from_hint_id` passed on submit; reset clears the hint id.
- `apps/frontend/app/page.tsx` -- `hintPrefill` state + `handleHintDeclare` (nonce-bumped); wires `prefill` into `ThesisStrip` and `onHintDeclare` into `Cockpit`.
- `apps/frontend/app/journal/page.tsx` -- the "Hints" view (tab + state + lazy load + render branch).

## Design discipline applied
- No business logic in the frontend — every value (evidence, citation, pattern label, setup/direction) is read off the backend hint object or the taxonomy; the dock/log derive nothing.
- All copy (dock title, register line, declare label/caption, declared-from label, log columns, empty-state) comes from `GET /research/taxonomy` with graceful fallbacks; no hardcoded labels.
- Design-system tokens only (amber-400/500/600/700/800/900 for the absorption/unclear semantics, slate surfaces, font-mono for stamps); loading/empty/error states styled.
- The new pages visually match the cockpit/journal style established by prior phases.

## Tests Run
Command: `cd apps/frontend && npm run build`
Result: exit 0 — type-check + compile clean. Routes: `/` 13.9 kB, `/journal` 5.95 kB.

## Known Issues
- Browser QA (the J-65 four legs + required-still-passing journeys J-01/J-04/J-06/J-38/J-51/J-59/J-63/J-64) is the next pipeline step — not run here. The hint card must coexist correctly with the thesis-strip lifecycle (the declare affordance hides once a thesis is active).
- A bound-socket dev-server smoke test could not run in this sandbox; the full path is proven by the backend's in-process ASGI integration tests (REST == WS `hint` key, declare-from linkage, pause-clears).
