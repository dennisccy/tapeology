**Verdict:** COHERENCE-PASS

## Iteration 9 — Coherence Audit

**Session:** i_will_be_super_rich_with_my_loved_ones
**Iteration:** 9 (goal-i_will_be_super_rich_with_my_loved_ones-iter-9)
**Snapshot SHA:** 3f24420b7542944eb25945a72b57f2b95503821c

---

## Step 1 — Data Contract Check

### Row 15 — Thesis projection (additive extension per blueprint notes)

Blueprint row 15 was additively extended by the decomposer before this iteration ran: a surviving
entry-marked active thesis on a stopped/mismatched watch is served by the SAME projection path
and the SAME endpoint (`GET /research/thesis/active?ticker=`) as a live thesis, flagged with an
explicit `not_evaluated` `monitor_status` and a backend-owned notice.

The implementation is faithful to that registered extension:

- A new **single** projection builder `build_projection` was introduced in
  `apps/backend/app/research/monitor.py` (line ~134). This consolidates what was previously an
  inline dict build inside `ResearchMonitor.projection()` into one shared function. Both the live
  monitor path (`ResearchMonitor.projection()`) and the registry's unwatched-survivor fallback
  (`ResearchRegistry._surviving_projection()` in `routes.py`) call this same function. There is
  no second computation path — this is a consolidation (one owner, not two).

- `ResearchRegistry._surviving_projection()` (`apps/backend/app/research/routes.py` ~line 143)
  calls `build_projection(...)` with `snapshot=None` (so statement statuses yield `not_yet`
  honestly) and routes through `GET /research/thesis/active` via the existing
  `registry.projection_for(ticker)` → `routes.py` handler. The registered canonical endpoint is
  unchanged. No second endpoint, no client-side recomputation.

- The frontend (`apps/frontend/app/page.tsx` lines 143–145) fetches the canonical
  `GET /research/thesis/active?ticker=` after a Stop and reads `monitor_status` verbatim to
  decide whether to show the surviving thesis. It does not recompute lifecycle state client-side;
  it reads `monitor_notice` verbatim from the projection (data-contract row 24). The
  `monitor_status === "not_evaluated"` check at `page.tsx:145` is a routing decision (which
  component to render), not a recomputation of the thesis value.

No duplicate computation of row 15. No non-canonical source. No violation.

### Row 16 — Verdict timeline / gap events (additive extension per blueprint notes)

Blueprint row 16 was additively extended: `watch_restarted` gap events are appended timeline
rows written by the same single writer, never edits or backfill.

The implementation (`apps/backend/app/research/monitor.py::_maybe_adopt_surviving`, ~line 336)
appends a `VerdictEventRecord` with `verdict="watch_restarted"` via `self._store.append_verdict_event()`
— the same single-writer queue. The `_restart_gap_appended` guard ensures idempotence (exactly one
append per re-attach). No second writer, no backfill. No violation.

### Row 24 — Taxonomies + display copy

New copy functions (`not_evaluated_notice`, `mismatched_source_notice`) were added to
`apps/backend/app/research/taxonomy.py`. These are production of backend-owned display copy,
consistent with row 24's registered owner (the backend taxonomy module). The frontend renders
`thesis.monitor_notice` verbatim. No violation.

### New displayed value: `monitor_status: not_evaluated`

The `not_evaluated` enum value is additive to the existing `monitor_status` field (already registered
in row 15 as `"ok" | "failed"`). It extends the same field, served from the same endpoint, computed
by the same projection builder. It is not a new independent concept — it is a new enum member of an
existing registered concept. The decomposer registered this extension in blueprint row 15's additive
note before the iteration ran. No violation; not a new unregistered value.

**Part A result: no violations.**

---

## Step 2 — Information Architecture Check

The iteration spec explicitly states: "No new surfaces. J-47's registered home is already `/` thesis
strip + `/journal` row (Cockpit / Journal) in blueprint.md."

Surfaces changed by this iteration (derived from the diff, no UI surface map available):

- `apps/frontend/components/ThesisStrip.tsx` — adds `NotEvaluatedThesis` component variant (rendered
  within the thesis strip area on the existing `/` Cockpit route). No new route introduced.
- `apps/frontend/app/page.tsx` — adds `survivingThesis` state and conditionally renders
  `<ThesisStrip>` + `<IdleState>` within the existing `/` Cockpit surface. No new route.
- `apps/frontend/lib/api.ts` — adds `fetchActiveThesis` function calling the canonical
  `GET /research/thesis/active?ticker=` endpoint. No new route.
- `apps/frontend/lib/types.ts` — additive `monitor_status` enum extension. No new route.

All frontend changes land within the existing `/` Cockpit route, which is the blueprint's
canonical home for J-47 (`/` thesis strip, Cockpit section, ≤1 click — it is the home route).
The journal-row leg of J-47 is verified via REST `GET /research/journal/{id}` per the established
convention; the `/journal` page is J-55's scope and is not introduced here.

No new pages, no nav-skeleton changes, no parallel shell introduced. The `NotEvaluatedThesis`
presentation variant is a new component inside the existing `/` surface, not a new route.

Nav file inspected: `apps/frontend/components/TopBar.tsx` — unchanged by this iteration.
The `/` Cockpit is reachable as the home route (0 clicks). No navigation path violation.

**Part B result: no violations.**

---

## Step 3 — Advisory Notes

None. No labeling inconsistencies, no formatting drift, no unregistered-but-new values. The
`monitor_status: not_evaluated` extension was registered in blueprint row 15 by the decomposer
concurrently with this spec, consistent with the actual implementation.

---

## Summary

No objective violations in Part A (Data Contract) or Part B (Information Architecture). The
surviving-thesis projection has exactly one computation path (`build_projection` in `monitor.py`),
called identically by the live monitor and the unwatched-survivor fallback — the "numbers don't
match" failure mode is structurally prevented. The `watch_restarted` gap event uses the existing
single writer queue with an idempotence guard. All UI changes land in the blueprint's canonical
home for J-47 (`/` thesis strip, Cockpit). COHERENCE-PASS.
