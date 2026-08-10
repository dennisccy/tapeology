# Iteration 3 — Coherence Audit

**Iteration:** goal-playbook-iter-3
**Date:** 2026-08-10
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Iter spec's own "Data-contract additions" field: none — this iteration is a pure UI consumer of
three rows already registered/shipped at baseline (J-01/J-02). Verified against the diff and the
blueprint's registered rows:

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Playbook records (signals + measurements + baseline + summary) | OK | Backend owner untouched behaviorally — `desk_playbook.py` diff is only the `side_sign` consolidation and the seed-collision fix (proved no-op by TC-11/TC-12 tests), zero diff to the route shape. UI reads it via `fetchDeskPlaybook` → `GET /research/desk/playbook?date=\|?id=` (`apps/frontend/lib/api.ts:950-974`), no client-side recompute — `PlaybookSectio`n's own copy states "read verbatim from GET /research/desk/playbook. Nothing here is recomputed in the browser" (`apps/frontend/app/desk/page.tsx:733`). |
| Playbook compute progress | OK | `desk_playbook_compute.py` untouched by this diff (not in the changed-file list). UI reads/starts it via `triggerDeskPlaybookCompute`/`fetchDeskPlaybookCompute`/`cancelDeskPlaybookCompute` → `POST/GET/POST-cancel /research/desk/playbook/compute[/cancel]` (`apps/frontend/lib/api.ts:980-1044`). |
| Playbook run ledger | OK | `desk_playbook_log.py` untouched. UI reads it via `fetchDeskPlaybookRuns` → `GET /research/desk/playbook/runs?session_date=` (`apps/frontend/lib/api.ts:1051-1073`). |
| Forward measurement shape reused for a playbook signal (`DeskForwardTouch`) | OK | `PlaybookSignalForward` (`apps/frontend/app/desk/page.tsx`) renders a signal's `forward` block through the existing `ForwardTouchTable`/`ForwardAvgCellView` components VERBATIM (defined once at `page.tsx:2220`/`2444`, not redeclared) — a reuse of an existing renderer for an already-byte-identical-by-construction shape, not a second implementation. |
| Playbook long/short sign multiplier (new this iteration, not a Data-Contract row — an internal computation, not a displayed value) | OK — consolidation, not a duplication | Three previously-duplicated inline literals (`desk_playbook.py`'s `_measure_signal` + `compute_playbook`'s baseline-draw branch, `desk_playbook_detect.py`'s `_market_block`) now all call one new `side_sign()` in `desk_playbook_features.py:298-313`. Guard-tested (`test_desk_playbook.py`'s `test_no_playbook_module_still_writes_the_inline_sign_literal` / `test_no_playbook_module_imports_desk_forwards_side_sign`) that the literal appears nowhere else and no playbook module imports `desk_forward._side_sign`. `desk_forward.py` itself carries zero diff (confirmed: absent from the changed-file list; `git diff <snapshot>..HEAD -- apps/backend/app/research/desk_forward.py` is empty) — this is the anti-goal's "single source of truth" requirement being actively enforced, not violated. |

No new UI surface fetches a registered value from a non-canonical endpoint or recomputes one
client-side. No new displayed value/entity appears this iteration that isn't already a field on the
already-registered "Playbook records" row (geometry/volume/market/disclosures/baseline summary are
all part of that one row's already-shipped shape, per the iter spec's own "New information
displayed" section — first-time rendering, not a new value).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Playbook Signals section, `/desk` | OK | `apps/backend/app/meta.py:31-34`'s `UI_ROUTES` carries zero diff against the snapshot (still exactly `/`, `/structure`, `/desk`, all `nav: True`) — no new route, no nav-skeleton edit, matching the iter spec's own "Blueprint conformance" claim. The section is added as a new `<section aria-label="Playbook Signals">` inside the existing `DeskPage` component (`apps/frontend/app/desk/page.tsx:955-968`), rendered below every shipped section — not a parallel shell, not a second page. It is reachable in exactly the same 1 click as `/desk` already was (top nav → Desk), matching the blueprint's pre-registered IA row ("Playbook Signals section (J-03) ... `/desk` (new section)"). |

No duplicate home introduced — no second "Desk" or "screening" page. No parallel layout/nav —
the section reuses the page's existing `Panel` wrapper and shell.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The playbook record's own field name for its per-(setup,side) pool is `signals` (vs. the forward
  rail's `touches`) — `apps/frontend/lib/types.ts`'s `DeskPlaybookSummaryCell` comment documents
  this as a deliberate vocabulary difference ("the playbook's OWN `{signals, baseline}` split ...
  the forward rail's vocabulary for a wall's price touches has no playbook analogue"), not an
  unexplained inconsistency. Noted for completeness only — not a coherence defect.
- `docs/goal.md`'s J-04/J-05/J-06 detector families will extend the same signal shape into the same
  section (per the iter spec's OUT OF SCOPE note); worth re-checking in a future audit that those
  families don't grow a second table/section instead of extending this one, but nothing in this
  iteration's diff suggests that risk — it is purely forward-looking.
- `README.md`'s one-line diff in the snapshot-to-HEAD range ("Current capabilities (iter-22):" →
  "Current capabilities:") was already committed in iter-2's showcase commit (`7ad422b`), not part
  of this iteration's actual work — harness/showcase bookkeeping, outside review scope.
