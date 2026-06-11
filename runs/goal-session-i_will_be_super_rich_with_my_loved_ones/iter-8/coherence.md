**Verdict:** COHERENCE-PASS

## Iteration 8 — Coherence Audit

**Session:** i_will_be_super_rich_with_my_loved_ones
**Iteration:** 8 (goal-i_will_be_super_rich_with_my_loved_ones-iter-8)
**Snapshot SHA:** 9197837cafaf345c31bd4bb51231a4182faabff8

---

## Step 1 — Data Contract Check

### Row 18 — Action marks (additive extension)
Blueprint registered owner: `POST /research/thesis/{id}/action`, served via row-15 projection + `GET /research/journal/{id}`.

This iteration extends row 18 additively by stamping `spread_at_mark` at recording time. The canonical owner and serving endpoints are unchanged. The new `spread_at_mark` column is added via a versioned schema migration (v2 → v3 in `apps/backend/app/config.py`, `apps/backend/app/research/store.py`). No duplicate computation. No violation.

### Row 27 — Realized move in R + R basis (new, registered this iteration)
The iteration introduced a new `marks_projection` function in `apps/backend/app/research/marks.py` as the single canonical computation owner. Both consumers call this same function:
- `apps/backend/app/research/monitor.py:345` — for the WS / row-15 thesis projection
- `apps/backend/app/research/routes.py:186,602` — for `GET /research/journal/{id}` and the `POST /research/thesis/{id}/action` response

The frontend (`apps/frontend/components/ThesisStrip.tsx`) reads `marks.realized_r` verbatim from the projection at lines 330–342. No client-side arithmetic. The blueprint was updated in this iteration to register row 27 with `marks_projection` as the single owner and row-15 + `GET /research/journal/{id}` as the serving endpoints. Blueprint update is consistent with the actual implementation. No duplicate computation, no non-canonical source. No violation.

### `directional_impact` fix
The dominance-rule rewrite (`apps/backend/app/research/monitor.py`, lines 70–111) corrects the status logic of an existing row-15 field (`statements[].status`). It introduces no new displayed value and no new computation owner — it only fixes the ordering of the adverse/favorable evaluation within the single existing `_evaluate_statement` function. No data-contract violation.

**Part A result: no violations.**

---

## Step 2 — Information Architecture Check

The iteration spec explicitly states: "No new pages; no nav-skeleton change; no reapproval needed."

Inspected surfaces from the diff:
- `apps/frontend/components/ThesisStrip.tsx` — mark controls, recorded-marks line, realized-R readout, conditional Abandon added to the thesis strip. All within the existing `/` (Cockpit) route.
- `apps/frontend/app/page.tsx` — passes `last` prop to `ThesisStrip`. No new route.
- `apps/frontend/lib/api.ts` — adds `recordAction` function. No new route.
- `apps/frontend/lib/types.ts` — adds `ActionMark` and `ThesisMarks` interfaces. No new route.

The blueprint IA canonically homes J-52 at `/` thesis strip (Cockpit) under "J-38–J-46, J-49, J-50, J-52, J-53". The changes land in that exact location. No new pages, no nav-skeleton changes, no parallel shell introduced.

Nav file inspected: `apps/frontend/components/TopBar.tsx` — unchanged by this iteration; multi-page nav (Cockpit/Journal/Studies) is not yet built (Journal page J-55 and Studies page J-60 are future iterations). The `/` Cockpit is reachable as the home route (0 clicks).

**Part B result: no violations.**

---

## Step 3 — Advisory Notes

None. No labeling inconsistencies, no formatting drift, no unregistered-but-new values. Row 27 was registered in the blueprint concurrently with its implementation, consistent with the decomposer's declared data-contract addition.

---

## Summary

No objective violations in Part A (Data Contract) or Part B (Information Architecture). The realized-R computation has a single canonical owner (`marks_projection` in `marks.py`) called identically by both the WS projection path and the journal-detail endpoint — the "numbers don't match" failure mode is structurally prevented. All UI changes live in the blueprint's canonical home for J-52 (`/` thesis strip). COHERENCE-PASS.
