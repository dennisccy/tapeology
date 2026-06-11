# goal-i_will_be_super_rich_with_my_loved_ones-iter-7 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-7
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

J-50 resolve controls on the cockpit thesis strip (`/` only — no new pages, no nav change).

- **`apps/frontend/components/ThesisStrip.tsx`** — on an ACTIVE thesis, the strip now renders two
  record-action controls below the existing details: **Played out** and **Abandon**. Each calls the
  new `resolveThesis(thesis.id, resolution)` client.
  - The controls render ONLY on a live thesis (`canResolve = !isInvalidated`). A system-owned
    `invalidated` thesis keeps its existing terminal treatment ("Thesis invalidated — resolved") and
    shows NO user controls — invalidated/expired are not user-resolvable.
  - On success the strip does NOT manually mutate state: the backend detaches the monitor, so the
    next WS frame carries `thesis: null` and the strip returns to the declare affordance on its own
    (the frontend derives nothing — single source of truth = the WS `thesis` key). The pressed
    button stays in a disabled "Resolving…" state in the brief interval before unmount, preventing a
    double-submit.
  - **Error handling:** a 409 (already-resolved / entry-marked-refuses-abandon) or 422 surfaces an
    explicit inline message (`data-testid="resolve-error"`, `role="alert"`) read VERBATIM from the
    backend `detail` — no swallowed failure, no dead click. The thesis stays active (nothing was
    resolved), so the controls stay available to retry.
  - Copy is descriptive/thesis-attributed ("Close out your thesis:", "Played out", "Abandon"),
    never imperative or predictive.
- **`apps/frontend/lib/api.ts`** — `resolveThesis(thesisId, resolution)` POSTs to
  `/research/thesis/{id}/resolve`; returns `{ok}` on success or `{ok:false, error}` with the backend
  detail surfaced verbatim; a transport failure degrades to "Backend unreachable".

## Design-system conformance

- Reuses the existing strip palette/tokens: slate-800 bordered buttons matching the declare/cancel
  affordances, `disabled:opacity-50`, hover/focus/active states on both controls. No new colors,
  spacing, or effects introduced. The controls sit under a `border-t border-slate-800 pt-3`
  separator consistent with the strip's existing footer treatment.
- No raw arbitrary values; all classes use the established Tailwind token set.

## States handled

- **Happy path:** click → "Resolving…" disabled state → WS pushes `thesis: null` → strip shows the
  idle declare affordance.
- **Error (409/422):** inline rose alert with the backend message; controls re-enabled; thesis stays
  active.
- **Invalidated (system-owned):** no controls shown — terminal treatment only.
- **Idle / declaring:** unchanged from prior iterations.

## Test data-testids (for browser QA)

- `thesis-resolve` (the control group), `resolve-played-out`, `resolve-abandon`, `resolve-error`.

## Tests Run

Command: `cd apps/frontend && NEXT_DIST_DIR=.next-dev-check npx next build`
Result: Compiled successfully + TypeScript type-check clean. (Throwaway dist dir + tsconfig/next-env
build artifacts reverted afterward.)

## Known Issues

- No new page; the journal-row-appears clause of J-50 is verified by REST (`GET
  /research/journal/{id}`), not a `/journal` UI (J-55 scope).
- The entry-marked-refuses-abandon path has no UI surface yet (no entry-mark control until J-52); the
  backend guard is unit-proven. If QA somehow reaches that 409 via a directly-injected entry mark,
  the inline error message renders correctly.
