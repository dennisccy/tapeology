# goal-i_will_be_super_rich_with_my_loved_ones-iter-8 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-8
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

### 1. Dominance rule for `directional_impact` (restore J-42)
- `apps/backend/app/research/monitor.py::_evaluate_statement` — replaced the iter-6/7
  adverse-fires-first ordering with a TRUE favorable-vs-adverse **dominance** comparison composing
  ONLY the existing primary-window `buy_price_impact` / `sell_price_impact` (read verbatim from the
  snapshot) against the classifier's own config-owned cutoffs (`min_buy_price_impact` /
  `max_sell_price_impact`). Semantics: neither material → `not_yet`; only favorable material → `met`;
  only adverse material → `violated`; **both** material → the side with the larger impact **magnitude**
  rules (plain magnitude comparison — no tolerance/ratio, so **no new config value, no fingerprint
  change**). Docstring updated to match the implemented rule.
- Truth anchors hold (proven by the four-quadrant unit tests): SIM-BUYER long (buy +0.42 vs sell
  −0.14) → **met**; SIM-SELLER long (sell dominant) → **violated**; SIM-BUYER short → **violated**;
  SIM-SELLER short → **met**; genuinely flat → `not_yet`. iter-6 direction-awareness preserved: an
  incidentally positive buy_impact on a falling tape still reads `violated` for a long (adverse sell
  dominates).

### 2. Action marks: Mark entry / Mark exit (J-52)
- **`POST /research/thesis/{id}/action`** (`apps/backend/app/research/routes.py`): body
  `{kind: "entry"|"exit", price}`. Records the mark **verbatim** (price exactly as submitted — never
  inferred, never a simulated fill), stamped at the current logical + wall time with **spread-at-mark**
  taken once from the current snapshot at recording. Guard matrix: 404 unknown thesis; 422 unknown
  kind / non-positive or non-finite price (a non-numeric body is a 422 at the pydantic layer); 409
  already-resolved / duplicate entry / duplicate exit / exit-before-entry. Writes go through the
  store's single writer queue (`BEGIN IMMEDIATE`), never the event/WS path.
- **Schema migration v2 → v3** (`store.py` + `config.py`): the `actions` table gains a
  `spread_at_mark` column via an idempotent, guarded `ALTER TABLE` inside one `BEGIN IMMEDIATE`
  writer transaction; `journal_schema_version` bumped 2 → 3 (excluded from `config_fingerprint`, so
  the fingerprint is unchanged). No backfill — a pre-existing action row keeps `NULL` spread_at_mark.
  Proven against a committed v2-schema fixture (`tests/fixtures/journal_v2_schema.sql`) + a
  persistent-DB reopen check.
- **Single realized-R projection** (`apps/backend/app/research/marks.py`, NEW): one
  `marks_projection(thesis, actions)` function computes `R = |entry − invalidation|`, the signed
  realized move in R after both marks (positive = move in the thesis's favor; long/short symmetric),
  and carries spread-at-mark per mark. Absent (null) without marks — no dishonest zero. A degenerate
  `R == 0` yields a `None` realized move (never a divide-by-zero / fabricated infinity). Both the
  row-15 thesis projection (REST `/thesis/active` ≡ WS `thesis` key) and `GET /research/journal/{id}`
  call THIS function — identical values by construction, no second path, no client math.
- **Abandon-withdrawal fact surfaced once**: the projection's `marks.has_entry` (derived from the
  persisted action rows) is the backend-owned fact the UI reads to withdraw Abandon. The existing
  entry-marked-refuses-abandon 409 guard stays green (now also exercised through the live endpoint).

### 3. Frontend — thesis strip only (no new pages / nav / chart)
- **Mark entry / Mark exit controls** (`apps/frontend/components/ThesisStrip.tsx`): on an active
  thesis, a last-prefilled, editable price field + Mark entry (until entered) then Mark exit (once
  entered). Submits verbatim via the new `recordAction` in `lib/api.ts`. Inline `role=alert` error
  display (consistent with the iter-7 `resolve-error` pattern); buttons disable during submit; no
  silent dead-clicks.
- **Recorded marks + realized-R display**: the strip shows the recorded entry/exit (price in mono +
  spread-at-mark) and, after both marks, the realized move in **R units** in mono, labeled a
  "journaled measurement, R = |entry − invalidation|" with spread-at-exit beside it. Never currency,
  never profit/loss framing.
- **Entry-marked ⇒ no Abandon**: the Abandon control is **not rendered at all** once
  `marks.has_entry` is true (closing J-50's deferred clause). An unmarked thesis still shows Abandon
  (J-50 must not regress). Played out + Mark exit remain.
- The current `last` is passed from `app/page.tsx` into the strip to prefill the mark price.

## Files Changed
- `apps/backend/app/research/monitor.py` -- dominance rule in `_evaluate_statement`; marks added to the projection
- `apps/backend/app/research/marks.py` -- NEW: the single marks + realized-R projection function
- `apps/backend/app/research/routes.py` -- `POST /thesis/{id}/action` endpoint; marks added to `/journal/{id}` + action route projection
- `apps/backend/app/research/store.py` -- `actions.spread_at_mark` column; v2→v3 migration; `ActionRecord`/`insert_action`/`get_actions` carry spread
- `apps/backend/app/config.py` -- `journal_schema_version` 2 → 3 (excluded from fingerprint)
- `apps/backend/tests/fixtures/journal_v2_schema.sql` -- NEW: committed v2-schema fixture for the v2→v3 migration test
- `apps/backend/tests/test_journal_migration.py` -- v2→v3 migration tests + updated version assertions to the current target
- `apps/backend/tests/test_research_action.py` -- NEW: action endpoint guard matrix, verbatim/spread/realized-R, WS parity
- `apps/backend/tests/test_research_marks.py` -- NEW: pure-function realized-R / signed-by-direction / degenerate-R / no-marks tests
- `apps/frontend/components/ThesisStrip.tsx` -- mark controls, recorded-marks line, realized-R readout, conditional Abandon
- `apps/frontend/lib/api.ts` -- `recordAction()` function
- `apps/frontend/lib/types.ts` -- `ActionMark` / `ThesisMarks` types; `marks` on `ThesisProjection`
- `apps/frontend/app/page.tsx` -- pass `last` (snapshot.market.last) into `ThesisStrip`

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **411 passed, 1 skipped** (baseline was 383 passed / 1 skipped — 28 new tests, no regressions).
Frontend build: `cd apps/frontend && NEXT_DIST_DIR=.next-qa npm run build` → compiled + type-checked successfully (isolated dist dir per the iter lesson; auto-generated `next-env.d.ts` reverted afterward).

Key suites verified green: `test_research_monitor` (four-quadrant directional_impact), `test_research_action`,
`test_research_marks`, `test_journal_migration` (v1→v2→v3 chained + v2→v3 + no-backfill + idempotent + persistent reopen),
`test_research_resolve` (entry-marked-refuses-abandon still green), `test_observer_equivalence` (engine untouched),
`test_verdict_engine`, `test_research_api`, `test_research_store`.

## Service / boot verification
- Backend boots cleanly: uvicorn on a throwaway port returned `GET /health` 200 and
  `GET /research/taxonomy` (4 setups); the FastAPI lifespan startup-sweep ran without error. Server
  shut down; no lingering `uvicorn`/`next dev` processes.
- `config_fingerprint` confirmed **unchanged** across the schema bump (`a7cf4d295b7404fc` before and
  after) — the dominance rule added no config value, and `journal_schema_version` is in the
  fingerprint exclusion set. Existing committed research records keep their stamp.

## Known Issues / Notes for QA
- **J-52 chart clause is DEFERRED to J-48** (per the spec / the J-45→J-48 convention): no chart
  geometry layer exists yet, so "marks appear on the chart" is intentionally NOT built this
  iteration. The strip/journal/verbatim/R clauses are complete. State this deferral in the QA report
  so the clause is tracked, not dropped.
- **Browser-capture precondition (binding):** restart the QA backend after this dev pass and run the
  server-freshness canary before any capture — `monitor.py` / `routes.py` / `store.py` were patched;
  a capture against a stale server is void.
- **Mandatory four-quadrant pixels** for the dominance change: J-42 (SIM-BUYER long CONFIRMING + stmt2
  MET) AND J-41 (SIM-SELLER long REJECTING + stmt2 VIOLATED) must BOTH be re-captured — they exercise
  the same `_evaluate_statement` path. J-50 non-regression: an UNMARKED thesis still offers + executes
  Abandon. J-52: prefill = current last, recorded verbatim, realized R + spread-at-mark shown,
  no-Abandon-once-entered in pixels, and a `GET /research/journal/{id}` readback of both marks.
- Marks read on the WS `thesis` key every push interval (0.2s) via a short-lived SQLite read
  connection — read-only over the engine, never a write on the WS/event path (capability-28
  discipline preserved). WAL allows the concurrent read; transitions/marks are infrequent.
- No external integrations / native deps added this iteration (research layer only).
