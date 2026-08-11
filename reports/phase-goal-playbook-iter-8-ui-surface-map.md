# Phase goal-playbook-iter-8 — UI Surface Map

**Phase:** goal-playbook-iter-8
**Date:** 2026-08-11
**Written by:** ui-impact-analyst

---

## File Classification

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/research/desk_playbook_evidence.py` (new) | backend-internal → consumed | indirect | New fold/cache module; has no route of its own but is called exclusively by the new `GET /research/desk/playbook/evidence` route, which the frontend consumes (confirmed below) |
| `apps/backend/app/research/desk_routes.py` | backend-api | direct (confirmed consumed) | Wires `GET /research/desk/playbook/evidence` (+ `?signature=`); `apps/frontend/lib/api.ts` calls this exact path via `fetchDeskPlaybookEvidence` |
| `apps/backend/app/research/desk_playbook_backscan.py` | backend-internal (bug fix) | indirect (behavior change on an already-consumed endpoint) | `_planned_dates` now catches `ValueError` on a malformed date and returns an empty plan instead of raising — changes the response of the already-UI-consumed `GET .../backscan/plan` |
| `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` | config/tooling | none | Extends the mandatory scoped-backend launcher for the deterministic replay lane; test infrastructure only |
| `apps/backend/scripts/seed_playbook_iter8_evidence_fixture.py` (new) | config/tooling | none | Seeds a disposable fixture corpus for QA/replay; never runs against the operator's real store |
| `apps/backend/tests/test_desk_playbook_evidence.py` (new) | backend-internal (tests) | none | Unit/integration coverage for the new module; no UI surface itself |
| `apps/backend/tests/test_desk_playbook_backscan.py` | backend-internal (tests) | none | Adds malformed-date coverage for the backscan-plan fix |
| `apps/backend/tests/test_desk_playbook_guards.py` | backend-internal (tests) | none | Retires a forward guard now that the evidence module exists; import-graph guard only |
| `apps/backend/tests/test_desk_ui_guards.py` | backend-internal (tests, UI-adjacent) | none (verification only) | Extends `_PRICE_ARITHMETIC_FIELDS` so the guard test source-scans the new frontend fields for illegal client-side arithmetic — does not itself render anything |
| `apps/frontend/app/desk/page.tsx` | frontend-direct | direct | New `PlaybookEvidenceSection`/`PlaybookEvidenceCellsTable`/`PlaybookEvidenceBreachTable`/`PlaybookEvidenceOtherSignatures` components + new "Playbook Evidence" `<section>`/`Panel` rendered on `/desk` |
| `apps/frontend/lib/api.ts` | frontend-direct | direct | New `fetchDeskPlaybookEvidence()` — the data-fetch layer feeding the new section |
| `apps/frontend/lib/types.ts` | frontend-direct | direct | New `DeskPlaybookEvidence*` types consumed by the new components |
| `runs/goal-session-playbook/journey-scripts/J-05.json` | test artifact | none | Golden replay script assertion fix (no longer collides with static copy); does not change product code or product UI |
| `runs/goal-session-playbook/journey-scripts/J-06.json` (new) | test artifact | none | New golden replay script for the already-shipped Range Trade / Double Top rows; exercises existing UI, does not add or change it |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `PlaybookEvidenceSection` — `Panel` titled "Playbook Evidence" (`<h2>Playbook Evidence</h2>`), `data-testid="desk-evidence-section"` | New section | J-08 ships a read-only fold of every recorded playbook signal into per-(setup, side, measure) distributions | Navigate to `http://localhost:3301/desk`, scroll to the bottom of the page, verify a panel headed "Playbook Evidence" is present below the Backscan panel |
| `/desk` | `PlaybookEvidenceCellsTable` (`data-testid="desk-evidence-cells-table"`), rows `data-testid="desk-evidence-cell-row"` | New table | Serves the setup × side × measure cross product (270 rows) with signal-vs-baseline stats | In the cells table, locate a row whose `data-testid="desk-evidence-signal-n"` cell shows a value ≥ 12 and verify its median/p25/p75/mean columns show numeric values (not blank, not "null") |
| `/desk` | `below_min_n` badge, `data-testid="desk-evidence-below-min-n"`, badge text "low n" | New badge/tag | Honestly flags cells with fewer than 12 recorded signals without filtering them out | Locate a cells-table row whose Flag column shows the amber "low n" badge; verify that row's signal median/p25/p75/mean columns still display numeric values (thin data is tagged, never hidden or nulled) |
| `/desk` | `PlaybookEvidenceBreachTable`, `data-testid="desk-evidence-breach-table"`, heading "Invalidation breaches" | New table | Serves `invalidation_breached` counts per setup/side/horizon (90 rows) | Scroll to the "Invalidation breaches" heading below the cells table; verify at least one row shows numeric values in both the "Breached" and "Total" columns |
| `/desk` | `PlaybookEvidenceOtherSignatures`, `data-testid="desk-evidence-other-signatures"`, heading "Other signatures (listed, never pooled)" | New conditional list | Lists any recorded signature other than the current default without pooling its records into the cells table | If the fixture rig has more than one recorded signature, verify the "Other signatures (listed, never pooled)" list appears with a signature string, a "N date(s)" count, and a created-span range; verify none of the setup/side/measure combinations recorded under that other signature change the counts already read from the cells table above |
| `/desk` | `PlaybookEvidenceSection` loading/empty/unavailable states — `data-testid="desk-evidence-loading"` / `"desk-evidence-empty"` / `"desk-evidence-unavailable"` | New states | Honest handling of in-flight load, zero recorded signals, and backend-unreachable, matching the page's existing per-section convention | Reload `/desk` and, if the network is fast enough to observe it, verify the animated loading skeleton briefly appears in place of the Playbook Evidence panel before resolving to the cells table |
| `/desk` | Backscan panel — "Backscan from day" input, `data-testid="desk-backscan-from-input"` | Changed behavior (bug fix) | A malformed/partial date no longer causes the backend plan endpoint to return HTTP 500 | Clear the "Backscan from day" field and type `2026-06-2` (a half-typed date); verify no element with `data-testid="desk-backscan-plan-error"` appears and the plan preview (`data-testid="desk-backscan-plan"`) reads "0 dates planned · 0 missing at the current signature." |
| `/desk` | Playbook Signals section — Capitulation row, `data-testid="desk-playbook-signal-setup"` containing "Capitulation" | Regression risk (golden script changed) | J-05's replay assertion was retargeted from the ambiguous substring "Capitulation" to a row-scoped selector; the underlying UI is unchanged but must be re-verified live | In the "Playbook Signals" date box (`data-testid="desk-playbook-date-input"`), type `2026-06-22`; verify a signal row appears whose setup cell reads "Capitulation" (symbol DECOR), then click "DECOR" and verify the text "euphoria recent" appears in the expanded detail |
| `/desk` | Playbook Signals section — Range Trade row (RTAAA) and Double Top row (DTAAA), `data-testid="desk-playbook-signal-range-trade-geometry"` / `"desk-playbook-signal-double-extreme-geometry"` | Regression risk (new golden script; owed screenshot delivered) | J-06 golden newly records this previously-unverified flow; a fresh Range Trade screenshot was owed since iteration 6 | In the "Playbook Signals" date box, type `2026-06-22`; verify a "Range Trade" row appears, click "RTAAA", verify the geometry line (`data-testid="desk-playbook-signal-range-trade-geometry"`) shows text including "MBR wide", "zone touches", "broke at slot"; then click the "Double Top" chip and verify the geometry line `data-testid="desk-playbook-signal-double-extreme-geometry"` appears |
| `GET /research/desk/playbook/evidence` | New REST endpoint (backend) | New API | Serves `cells`/`invalidation_breached`/`other_signatures`/`parameters`/`register` JSON; consumed by the `/desk` section above | `curl http://localhost:8301/research/desk/playbook/evidence` and verify the JSON body has a `"cells"` array with 270 entries and a non-empty string `"register"` field |
| `GET /research/desk/playbook/evidence?signature=<value>` | Query param — inspect-only mode (backend) | New API param, no UI control | Lets a caller inspect one named signature's `dates`/`created_span` without pooling it into any cell | `curl "http://localhost:8301/research/desk/playbook/evidence?signature=<a signature listed in other_signatures>"` and verify the response is exactly `{signature, dates, created_span}` (not the full cells payload) — this parameter is not reachable from any UI control |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/desk_playbook_evidence.py`'s `PlaybookEvidenceCache` (SQLite
  projection cache, stat-keyed) — a pure performance layer; cache cold vs. warm is verified
  byte-identical at the content level (TC-2/TC-6), so it affects only page-load latency, never what
  the operator sees.
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` — extended scoping of the
  mandatory deterministic replay-lane launcher so no golden-replay run can reach the operator's real
  `.data/` store — test/QA infrastructure only, no UI surface.
- `apps/backend/scripts/seed_playbook_iter8_evidence_fixture.py` (new) — seeds a disposable fixture
  corpus (12 synthetic members on 2026-06-25) for the scoped rig only — no UI surface.
- `apps/backend/tests/test_desk_playbook_evidence.py`, `test_desk_playbook_backscan.py`,
  `test_desk_playbook_guards.py`, `test_desk_ui_guards.py` — automated test coverage; verification
  artifacts, not product surfaces.
- `runs/goal-session-playbook/journey-scripts/J-05.json` (assertion fix) and `J-06.json` (new
  golden) — QA automation scripts that exercise already-existing UI rows; they do not add, remove,
  or change any UI surface themselves.

---

## Summary

- **Frontend surfaces changed:** 1 (`/desk` page — one new section containing 3 sub-tables/lists
  and 3 loading/empty/unavailable states)
- **New pages/routes:** 0 (no new route; `/desk` already existed, the new content is a scroll-down
  section)
- **Modified components:** 1 file (`apps/frontend/app/desk/page.tsx`), adding 6 new component
  functions (`PlaybookEvidenceCellRow`, `PlaybookEvidenceCellsTable`, `PlaybookEvidenceBreachRow`,
  `PlaybookEvidenceBreachTable`, `PlaybookEvidenceOtherSignatures`, `PlaybookEvidenceSection`) plus
  supporting changes in `apps/frontend/lib/api.ts` and `apps/frontend/lib/types.ts`
- **Navigation changes:** no
- **Backend-only changes:** 6 (evidence cache internals, the two QA/tooling scripts, and 4 test
  files)
