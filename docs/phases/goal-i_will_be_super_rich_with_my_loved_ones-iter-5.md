# Goal Iteration 5 — Versioned journal migration + atomic declaration: unblock and browser-prove the verdict engine (J-38, J-40–J-46)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-38, J-39, J-40, J-41, J-42, J-43, J-44, J-45, J-46, J-68
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-17, J-19, J-21, J-24
- **Anti-goal reminders:**
  - "**Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*"
  - "**Persistence stays scoped to research records.** SQLite holds theses, verdict events, hints, actions, reviews, and study results only — no trades, quotes, candles, or feature series are persisted (committed test fixtures excepted)."
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*"
  - "**No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect. *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect. *(critical)*"

## GOAL

A user can declare a thesis on the real, persistent dev installation and watch the verdict engine judge it live in the browser — the iter-4 schema-migration 503 and the orphaned-thesis 409 are gone, proven by a 200 declare against the persistent dev DB and a full 12-test browser matrix.

## BACKGROUND

This is the consolidation/fix iteration the iter-4 evaluator mandated (verdict CONTINUE, depth full, "no new feature scope until the above flips"). The verdict-transition engine for J-40–J-46 is built and unit-proven (21 new tests incl. the J-40 trap and the J-45 latch), but every browser journey was blocked by one persistence defect: `verdict_events` gained `rule_first_true_ts`/`rule_first_true_price` only in the `CREATE TABLE IF NOT EXISTS` DDL (`apps/backend/app/research/store.py:67-68`), with no versioned migration — `journal_schema_version` is still `1` (`apps/backend/app/config.py:362`, whose own comment says "migration is out of scope this iteration") and `_create_schema` (store.py:184-194) no-ops on the pre-existing dev DB (`apps/backend/tapeology_journal.db`). Every `POST /research/thesis` against that DB 503s at the initial verdict-event INSERT. A secondary defect — `insert_thesis` → `append_verdict_event` running as two transactions — left orphaned active thesis `4beae280…` (zero verdict events) that 409-blocks SIM-BUYER. Temp-DB unit tests and the QA-validation step structurally cannot see either defect.

**Binding lessons applied (from `state/lessons.md`):** (a) any `store.py` schema change MUST ship a versioned migration AND be checked against the persistent dev DB / a committed old-schema fixture; (b) multi-row creation must be one writer transaction; (c) every below-the-fold UI capture must scroll-into-view or be full-page; (d) QA must precondition-check the dev server and never `npm run build` against the live dev server's shared `.next` (use `NEXT_DIST_DIR=.next-qa`); (e) recount QA results from the result tables, not prose summaries.

Depth is **full** (evaluator-mandated): the change touches the persistence layer and data model, and the iteration's value is the complete 11-step verification pipeline — especially browser QA over the persistent DB and a closure audit that actually opens the PNGs.

## IN SCOPE

### Backend

- [ ] **Versioned SQLite migration (the blocker).** Bump `journal_schema_version` to `2` in `apps/backend/app/config.py` (and update its now-stale "migration is out of scope" comment). In `apps/backend/app/research/store.py`, on open: read the stored `schema_version`; when it is older than 2, run `ALTER TABLE verdict_events ADD COLUMN rule_first_true_ts REAL` and `ALTER TABLE verdict_events ADD COLUMN rule_first_true_price REAL`, then update the `schema_version` row — all inside one `BEGIN IMMEDIATE` writer transaction. A `PRAGMA table_info` guard is acceptable belt-and-braces (e.g. for a DB that already has the columns but a stale version row). The migration MUST NOT backfill `rule_first_true_*` for pre-existing rows — old events keep `NULL` (the timeline is append-only, never backfilled). Note `journal_schema_version` is already excluded from the config fingerprint (config.py:437) — keep it that way; a migration must not change `config_fingerprint`.
- [ ] **Atomic declaration.** `insert_thesis` + the initial `pending` verdict event execute in ONE writer transaction (single `BEGIN IMMEDIATE` … commit). A failure at any point rolls back both — a thesis row without its initial event can no longer exist.
- [ ] **Orphan cleanup via the startup sweep.** Verify the existing startup sweep resolves orphaned active thesis `4beae280…` (active, zero verdict events) to `expired` on backend start; extend the sweep if a zero-event active thesis is not currently handled. Do NOT delete the row — expired theses remain visible (no survivorship pruning). After the sweep, SIM-BUYER must accept a new declaration (no 409 from the orphan).
- [ ] **Old-schema regression test (the class temp-DB tests cannot see).** Commit a small iter-2-schema (v1) journal DB fixture under `apps/backend/tests/fixtures/` (research records only — explicitly allowed by the persistence anti-goal as a committed test fixture; NO tape data). A new test copies the fixture to a temp path, opens the store against it, asserts the schema migrates to v2 (columns present, version row updated, pre-existing rows intact with `NULL` rule_first_true), and successfully declares a thesis end-to-end.
- [ ] **Atomicity regression test.** Force a failure on the initial verdict-event insert (e.g. monkeypatched/fault-injected) and assert NO thesis row persists and the API surfaces the error honestly (no partial save, no orphan).
- [ ] **Minor (from iter-4 review):** fix the store.py docstring note the reviewer flagged.

### Frontend (if applicable)

- [ ] Add `data-testid="thesis-strip"` to the ThesisStrip root element (`apps/frontend/components/ThesisStrip.tsx`) — QA's test plan expects it; no other frontend change.

### New user-facing capability
Declaring a thesis now WORKS on the real, persistent installation (not just fresh temp DBs): the declare flow returns the active thesis instead of a 503, and the verdict engine's live judgements (pending → confirming / weakening / rejecting / invalidated, each with evidence) become visible in the browser for the first time.

### New information displayed
None new — the iter-4 verdict chip, evidence line, statement statuses, and terminal invalidated treatment finally render against real persisted data. No new value is introduced.

### New user actions
None new — the existing declare form simply stops failing.

### UI surface changes
None beyond the `data-testid` attribute. No new pages, panels, or nav changes.

### Product surface delta
The product crosses from "verdict engine exists in unit tests" to "verdict engine demonstrably judges a declared thesis in the running product" — the core J-40–J-46 experience becomes real for the user.

### Blueprint conformance
No new surfaces. All target journeys live at their registered home: `/` thesis strip (Cockpit) per the blueprint IA (J-38–J-46 row). Top-bar nav untouched.

### Data-contract additions
None. No new displayed value. The fix hardens the already-registered row 16 (published verdict timeline — verdict engine → journal repository, single writer queue) and row 15 (thesis projection) without adding owners, endpoints, or computations. A one-sentence persistence-discipline note (versioned migrations proven against a committed old-schema fixture) is added to `blueprint.md`'s Persistence paragraph — additive, no reapproval needed.

## OUT OF SCOPE

- ANY new feature scope (evaluator mandate): no thesis geometry on the chart (J-48), no entry risk flags (J-49), no user-facing resolve endpoint/controls (J-50), no `/journal` page (J-55–J-57), no action marks (J-52), no analytics (J-59), no studies (J-60–J-62), no cue layer (J-63–J-67 — gated on evidence anyway).
- No engine, classifier, feature, or provider changes of any kind.
- No verdict-rule changes — the verdict engine itself is unit-proven; this iteration only fixes persistence beneath it.
- No backfilling of `rule_first_true_*` onto historical verdict events.
- No DB framework/ORM introduction — stdlib `sqlite3` migration only, per the journal-store discipline.

## DEFINITION OF DONE

- [ ] `POST /research/thesis` returns 200 against the **persistent** dev DB (`apps/backend/tapeology_journal.db`, migrated in place to schema v2) — verified in the dev handoff with the actual dev DB, not a temp DB
- [ ] Orphan thesis `4beae280…` resolved to `expired` by the startup sweep; a fresh declaration on SIM-BUYER succeeds (no 409)
- [ ] Old-schema-fixture migration test and atomicity test pass; full backend suite green, no regressions
- [ ] Target journeys J-38, J-40, J-41, J-42, J-43, J-44, J-45, J-46 pass via browser-qa-agent against the persistent dev stack; J-39 (422/409/404 matrix incl. the inline-422-in-pixels clause) and J-68 (idle strip) re-captured
- [ ] EVERY browser capture obeys the binding evidence rule: the asserted element is in pixels via scroll-into-view or full-page screenshot — a chart-fragment capture of a below-the-fold assertion is a FAIL of the evidence requirement; the phase-closure-auditor opens the PNGs
- [ ] Required-still-passing journeys remain green
- [ ] No anti-goal violation introduced (timeline never backfilled; fixture contains research records only; engine untouched)
- [ ] `data-testid="thesis-strip"` present in the DOM
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-5-dev.md`

## TESTING REQUIREMENTS

- **Browser (full 12-test matrix, persistent dev DB, evidence rule mechanically enforced):**
  - J-38 — declare absorption_reversal/long on SIM-BIDABS; strip shows ACTIVE thesis with frozen statements + live statuses, verdict starts `pending`; REST `…/thesis/active` equals the WS `thesis` key verbatim; no reload
  - J-39 — unwatched ticker → 404; wrong-side invalidation → inline message + 422 **visible in pixels**; missing level (level_break) → 422; forbidden level (absorption_reversal) → 422; second active thesis → 409 with explicit message; nothing partially saved
  - J-40 — SIM-REVERSAL: pending through sustained absorption (premise met, trigger not-yet), confirming only on the flip to buyer control, timeline records `rule_first_true` + published
  - J-41 — SIM-SELLER + trend_continuation/long: rejecting with plain-language opposing-control evidence; thesis stays active
  - J-42 — SIM-BUYER + trend_continuation/long: confirming after dwell; no flapping
  - J-43 — SIM-SHIFT: confirming → weakening after the shift ("supporting evidence faded" register), never a silent return to pending; both transitions on the timeline
  - J-44 — SIM-SELLER, invalidation just below last: dwell-exempt invalidated + auto-resolve + terminal strip treatment + offending print as evidence
  - J-45 — SIM-BUYER + level_break/long, level above last: pending pre-cross however strong control; confirming after the latch (chart level-line clause stays deferred to J-48)
  - J-46 — SIM-REVERSAL + failed_move_fade/long: confirming DURING absorption (the deliberate J-40 asymmetry); remains confirming on the reclaim
  - J-68 — idle cockpit with no thesis: strip is a single declare affordance (now locatable via `data-testid="thesis-strip"`); capture mode/state shown must match the narrative (the iter-4 capture-narrative mismatch is a FAIL condition)
  - QA preconditions: verify the dev backend + frontend are the ones under test before any TC; never `npm run build` against the live dev server's shared `.next` (use `NEXT_DIST_DIR=.next-qa`); recount pass/fail from the result tables, not summaries
- **Unit/integration:** migration from the committed v1-schema fixture (columns added, version row = 2, old rows intact with NULL rule_first_true, declare succeeds); idempotent open on an already-v2 DB; atomic declaration rollback (no orphan on forced event-insert failure); startup sweep over a zero-event active thesis; existing 353-test suite green incl. observer equivalence.
- **Error cases:** declaration against an unmigrated-then-migrated DB must succeed (never 503); a partial declaration failure must surface an explicit error AND leave no thesis row; a stale version row with columns already present must not crash the open.

## NOTES

- Evaluator mandate (iter-4 eval, Next-Step Recommendation): items 1–5 of that list map 1:1 to this spec's Backend + Frontend scope; "No new feature scope until the above flips" is binding — the reviewer should reject any drift.
- Target-journey count exceeds the usual 1–3 deliberately: all ten are gated on a single persistence defect, the verdict engine behind them is already built and unit-proven, and the evaluator explicitly mandated re-running the full 12-test browser matrix in one fix-and-verify pass.
- Pipeline-discrepancy context for QA/closure: iter-4's QA-validation PASS was contradicted by browser QA an hour later (temp-DB masking), and the binding evidence rule has now been violated four iterations running — this iteration's closure gate must treat un-opened or mis-framed PNGs as CLOSURE-FAIL material.
- The audit step never produced `…-iter-4-audit.md` (run halted at `qa_complete`); running full depth ensures the audit executes this time.
- Coherence: iter-4 was COHERENCE-PASS with one advisory (transient taxonomy-label fallback race) — no action required this iteration; do not expand scope to chase it.
