# Phase goal-clean_slate-iter-6 — UI Surface Map

**Phase:** goal-clean_slate-iter-6 (J-05: "The kept product stands — regression sentinel")
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

Zero UI surfaces were modified by this iteration's own diff — 0 `.tsx`/`.ts` files changed
(confirmed via `git status` / `git diff --stat`: the only modified file anywhere is
`apps/backend/app/research/routes.py`, plus one new backend test file and one new evidence
report). The rows below are **not** new or changed surfaces. They are the pre-existing,
already-shipped surfaces that this iteration's own target journey (J-05) and required-still-passing
journeys (J-01–J-04) mandate re-walking, as evidence that the backend-only cleanup in `routes.py`
(which also serves several of `/structure`'s live routes, even though no live handler in it was
touched) left the shipped product byte- and behavior-identical. Every row's Change Type is
"Regression check (unmodified)."

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` (Cockpit) | Ticker watch flow — ticker input (`placeholder="Ticker e.g. SIM-BUYER"`) + "Watch" button + Tape State panel | Regression check (unmodified) | Not touched this iteration; re-walked because J-05 (this iteration's own target journey, `journey-scripts/J-05.json` step 1–3) must re-certify it after the `routes.py` cleanup | Type "SIM-BUYER" into the ticker field and click "Watch"; confirm the page displays the text "Buyer Control" |
| `/` (Cockpit) | Tape bar-size control (`aria-label="Tape bar size"`, 2nd button) | Regression check (unmodified) | Same journey, step 4 | Click the second button inside the "Tape bar size" control; confirm the caption text "Logical 30s bars built live from the tape." appears |
| `/` (Cockpit) | "Stop watching" button / idle state | Regression check (unmodified) | Same journey, step 5 | Click "Stop watching"; confirm the page returns to displaying the text "No ticker watched" |
| `/structure` | Load flow — symbol input (`placeholder="e.g. PG"`), as-of input (`placeholder="2026-06-09T21:00:00Z"`), "Load" button | Regression check (unmodified) | Same journey, steps 6–9 | Fill the symbol field with "AAPL" and the as-of field with "2026-06-22T21:00:00Z", then click "Load"; confirm the page displays the text "300.11" |
| `/structure` | Case Studies row → drill-in (`data-testid="case-studies-row"` → `data-testid="case-drillin"`) | Regression check (unmodified) | Same journey, step 10 | Click a `case-studies-row` element in the Case Studies table; confirm a `case-drillin` element appears |
| `/structure` | Edge Report panel + Compute button | Regression check (unmodified) | TC-10 requires a fresh confirmatory screenshot of its current honest state this iteration | View the Edge Report section; confirm it shows either populated edge cells or the exact text "Edge report not computed yet." together with a visible "Compute" button |
| Every kept page (`/`, `/structure`) | Top navigation bar | Regression check (unmodified) | TC-11 re-confirms the nav did not regrow back toward 5 items after this iteration's `routes.py` edit | Load `/`; confirm the top nav shows exactly two items, labeled "Cockpit" and "Structure", and no other link anywhere |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/routes.py` — deleted 5 orphaned Pydantic request-body classes
  (`ThesisRequest`, `ResolveRequest`, `ActionRequest`, `StudyRequest`, `ReviewRequest`) left behind
  by an earlier iteration's route demolition. Each had exactly one occurrence in the file (its own
  class definition) and zero live route-parameter references — confirmed dead code, unreachable
  from any page, button, or API call, before or after this change. No UI surface affected.
- `apps/backend/tests/test_routes_no_orphaned_request_models.py` — new backend guard test (2 test
  functions, AST-based structural check over `routes.py`'s own class/parameter shape). Runs only
  inside `pytest`; no UI surface.
- `runs/goal-session-clean_slate/iter-6/diff-vs-inventory-crosscheck.md` — new evidence/process
  artifact (extends iter-5's cumulative session diff-vs-inventory cross-check). Process
  documentation, not a product surface.
- 14 fully-deleted backend routes (e.g. `GET /research/journal`, `POST /research/studies`)
  reconfirmed returning HTTP 404 — a pure API-level re-verification; their corresponding frontend
  pages were already deleted in an earlier iteration, so there is no browser element left to click
  for these at all. `GET /research/taxonomy` reconfirmed HTTP 200 with its already-slimmed
  payload — this endpoint is consumed by the existing feed-basis badge, but its response shape is
  unchanged this iteration.
- MCP `list_tools()` reconfirmed to return exactly the 15 previously-established tool names —
  this is the AI-assistant/MCP integration surface, not the browser UI; there is no visual element
  to test.
- `README.md` — verified already correct (the 3 sentences the plan expected to need fixing were
  already absent, from an earlier iteration's documentation refresh); not edited this iteration.
  No UI impact either way.
- `runs/goal-session-clean_slate/telemetry.jsonl`, `runs/goal-session-clean_slate/trace/trace.jsonl`,
  `runs/goal-session-clean_slate/dispatch/*` — pipeline telemetry/dispatch bookkeeping. No UI
  impact.
- `docs/handoffs/goal-clean_slate-iter-6-dev.md`, `docs/phases/goal-clean_slate-iter-6.md`,
  `reports/phase-goal-clean_slate-iter-6-implementation-summary.md`,
  `reports/qa/goal-clean_slate-iter-6-test-plan.md`,
  `reports/reviews/goal-clean_slate-iter-6-review.md`,
  `runs/goal-clean_slate-iter-6/status.json` — pipeline process documentation for this iteration.
  No UI impact.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0 (the 7 rows above are unmodified regression-sentinel re-walks
  carried out as this iteration's own test evidence, not surfaces this iteration changed)
- **Navigation changes:** no (nav stays exactly "Cockpit" + "Structure", 2 items)
- **Backend-only changes:** 3 product/test files (`routes.py`, the new guard test, the
  diff-vs-inventory crosscheck) plus re-verification-only checks against already-shipped
  backend/MCP surfaces (404 sweep, taxonomy payload, MCP tool count) that have no UI element of
  their own
