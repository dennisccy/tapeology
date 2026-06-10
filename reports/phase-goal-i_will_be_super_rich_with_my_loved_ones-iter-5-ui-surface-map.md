# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-5 — UI Surface Map

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-5
**Date:** 2026-06-10
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `ThesisStrip` (`StripShell` root `<section>`) | Changed behavior | `data-testid="thesis-strip"` added to make the strip locatable in all states for browser QA (J-68 idle, J-38 active) | Query `[data-testid="thesis-strip"]` in the idle cockpit (no active thesis); confirm the element is present in the DOM and visible on screen |
| `/` | ThesisStrip — declare form submit | Changed behavior | Backend `POST /research/thesis` now returns 200 against the persistent DB (was 503); the strip transitions from idle to active on success | Watch SIM-BIDABS to `bid_absorption`, open the declare form, submit `absorption_reversal / long / invalidation 99.0`; confirm the strip switches to the active thesis view showing the verdict chip and evidence line (not a server-error message) |
| `/` | ThesisStrip — verdict chip | Changed behavior | Verdict engine judgements (pending → confirming / weakening / rejecting / invalidated) now render against real persisted data for the first time | After a successful declaration, wait ~4 s; confirm the verdict chip label and colour update from pending (slate) to confirming (emerald) as the engine judges the tape |
| `/` | ThesisStrip — inline validation messages | Changed behavior | 422/409/404 error messages were always coded but unreachable while declaration itself 503'd; now reachable on the persistent installation | In the declare form, submit a wrong-side direction (e.g. `trend_continuation / short` on a buyer-control tape); confirm the 422 error message is visible as text inside the strip, not hidden behind a toast or browser alert |
| `/` | ThesisStrip — terminal invalidated treatment | Changed behavior | The terminal rose-ring chip and offending-print evidence line were built in iter-4 but only reachable now that declaration succeeds | On SIM-SELLER with an active `trend_continuation / long` thesis, wait for invalidation; confirm the strip shows a rose-bordered chip with a `ring-1 ring-rose-500/50` terminal treatment and the offending print as evidence text |
| `/` | ThesisStrip — idle strip (J-68) | Changed behavior | `data-testid` attribute makes the idle affordance directly addressable; capture-narrative mismatch from iter-4 must not recur | Load the Cockpit with no active thesis (after expiry or fresh backend start); confirm `[data-testid="thesis-strip"]` resolves to the single-line declare affordance — no verdict chip, no statement list |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/config.py` — `journal_schema_version` bumped `1 → 2`; stale comment updated. No API response shape change; no UI surface affected.
- `apps/backend/app/research/store.py` — `_migrate()` method (v1→v2 on-open migration, one `BEGIN IMMEDIATE`), `insert_thesis_with_event()` (atomic declare), `_column_exists` guard, docstring fix. Persistence internals only; the API surface and response shapes are unchanged.
- `apps/backend/app/research/routes.py` — `declare_thesis` calls the single atomic `insert_thesis_with_event` instead of two separate calls. Route path, HTTP method, and response schema unchanged; only the error mode (partial save → full rollback) differs.
- `apps/backend/tests/fixtures/journal_v1_schema.sql` — committed v1-schema fixture for migration regression tests. Test fixture; no UI surface.
- `apps/backend/tests/test_journal_migration.py` — migration, idempotency, stale-version-row, atomic-rollback, and orphan-sweep tests. Tests only; no UI surface.
- `apps/backend/tests/test_research_api.py` (new route-level atomicity test) — asserts 503 + no orphan on forced event-insert failure. Tests only; no UI surface.
- `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` — one additive sentence in the Persistence paragraph. Internal project documentation; not user-facing.

---

## Summary

- **Frontend surfaces changed:** 1 (`ThesisStrip` at `/`)
- **New pages/routes:** 0
- **Modified components:** 1 (`ThesisStrip.tsx` — single `data-testid` attribute; no visual change)
- **Navigation changes:** no
- **Backend-only changes:** 7 (config, store, routes, fixture, 2 test files, blueprint doc)
