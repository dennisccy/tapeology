# Goal Iteration 13 — Execution checks + the /journal/[id] review-detail page (J-54, J-55)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 13
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-54, J-55
- **Required-still-passing journeys:** J-01, J-02, J-42, J-49, J-50, J-51, J-52, J-68
- **Anti-goal reminders:**
  - **Journal integrity.** "Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned." *(critical)*
  - **No naked outputs.** "Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect." *(critical)*
  - **Single source of truth.** "Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views." *(critical)* — extended by the Data Contract: execution checks are computed ONCE at resolution and served by ONE endpoint, never recomputed at read.
  - **Evidence before cues.** "The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect." *(critical)*
  - **No profitability or edge claims.** "No currency P&L, equity curves, compounding, or win-rate-as-edge presentation anywhere. R statistics are journaled measurements and MUST always appear with their n, the abandonment bucket, the null baseline (where one applies), and the spread/R cost figure." *(critical)*
  - **No prediction language.** "A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do." *(critical)*

## GOAL

A resolved thesis can be opened at `/journal/[id]` and reviewed honestly: frozen expected-behaviour statements with final statuses beside the verbatim verdict timeline at true clock time, plus machine-derived execution checks (computed once at resolution, with evidence) that auto-suggest mistake tags the user can see pre-selected and edit.

## BACKGROUND

The iter-12 evaluator's mandated next step is exactly this pair: J-54 (objective execution checks) + J-55 (the review-detail page). All raw material exists and is verified in pixels: action marks with logical + wall timestamps and spread-at-mark (iter-8), `rule_first_true` on every timeline row (iter-4), gap events + interruption-safe lifecycle (iter-9), frozen `risk_flags` (iter-11), the `/journal` list page with the persistent nav (iter-12), and `GET /research/journal/{id}` already serving the thesis + marks + append-only timeline verbatim (blueprint rows 16/18/19). The `/journal/[id]` route is ALREADY in the approved IA blueprint under the Journal home — building it is additive, no nav-skeleton change, no reapproval needed. Depth stays lean per the evaluator (the FULL-pipeline harness defect at `qa_complete` remains open upstream; lean iterations 6–12 produced complete evidence).

Binding build order holds: J-56/J-57 (grades + review save flow) come next in iter-14; the evidence layer (J-58–J-62) after; cues (J-53, J-63–J-67) strictly last. This iteration ships the execution-checks half of Data Contract row 19; the grades half stays honestly absent.

## IN SCOPE

### Backend

- [ ] **Single-owner execution-checks function** (new module under `apps/backend/app/research/`, e.g. `execution_checks.py`): ONE pure function computing the four named checks from the persisted action marks + the append-only verdict timeline + the frozen thesis fields ONLY (goal.md capability 27 / J-54):
  - `entered_before_confirmation` — entry mark's logical_ts precedes the first published `confirming` event (or no confirmation was ever published while entry-marked);
  - `chased_entry` — entry price beyond the recorded `rule_first_true_price` + the config-owned chase return threshold, direction-aware; per Constraints, the chase check anchors at the recorded `rule_first_true` price, NEVER the post-dwell publish (reuse the existing config chase-threshold seam — no new magic numbers);
  - `exited_beyond_invalidation` — exit mark recorded beyond the declared invalidation in the adverse direction (held through the stop);
  - `cut_confirming_early` — exit recorded while the latest published verdict was `confirming` (before any weakening/rejecting/invalidation).
  Each check yields an **enum status** (e.g. `failed | passed | not_applicable` — labels, NEVER numeric scores) + plain-language evidence quoting the measured values (timestamps, prices, thresholds). No marks ⇒ the mark-dependent checks read an explicit `not_applicable`, never a fabricated pass/fail.
- [ ] **Computed once at resolution, persisted**: every terminal-resolution code path (user `POST /research/thesis/{id}/resolve`, the system invalidation auto-resolve, stream-end/stop expiry, and the restart-expiry sweep) invokes that SAME single function once and persists the result on the thesis row. **Schema v5 versioned migration** (bump `journal_schema_version` to 5, in-place `ALTER` inside one writer transaction, proven by a test against a committed v4 fixture — `CREATE TABLE IF NOT EXISTS` alone is never a migration). Pre-v5 resolved theses keep the key **ABSENT** (honest omission, like pre-v4 `risk_flags`) — never backfilled, never computed at read.
- [ ] **Suggested mistake tags**: the check→suggested-tag mapping is backend-owned; failed checks map to tags from the backend mistake-tag catalog (e.g. `entered_before_confirmation` → `entered_before_confirmation`, `chased_entry` → `chased`). Suggestions are derived once with the checks at resolution and persisted/served alongside them — the system SUGGESTS only; it never records a confirmed tag on its own.
- [ ] **Mistake-tag catalog in the taxonomy** (additive to `app/research/taxonomy.py` + `GET /research/taxonomy`): the full backend-owned catalog per goal.md capability 29 (`chased`, `entered_before_confirmation`, `ignored_rejection`, `ignored_risk_flags`, `moved_invalidation` *(self-assessed)*, `no_clear_setup`, `wrong_setup_type`, `overstayed`, `other` + required note) with display copy. The review SAVE flow (`POST …/review`) is NOT built this iteration (J-57, iter-14).
- [ ] **`GET /research/journal/{id}` gains additive keys** (`execution_checks`, suggested tags) served VERBATIM from the persisted record — the existing single serving path of Data Contract row 19; nothing recomputed at read; `verdict_events` write paths untouched (still append-only, no update/delete added).

### Frontend (if applicable)

- [ ] **`/journal/[id]` review-detail page** (new route under the existing Journal home), rendered entirely from the single `GET /research/journal/{id}` response + taxonomy labels:
  - the frozen expected-behaviour statements with their final statuses;
  - the verdict timeline at **true clock time** (persisted timestamps only, the one shared dd-MM-yyyy formatter; never elapsed playback seconds, no client-side re-derivation), each transition carrying its evidence verbatim, gap events shown explicitly;
  - the frozen entry risk-flag chips (taxonomy labels; key absent ⇒ honest "not assessed" copy, never an invented clean state);
  - action marks verbatim (price + time + spread-at-mark; realized move in R only when both marks exist — no marks, no realized metric);
  - **execution checks** with status + evidence; **suggested mistake tags pre-selected and toggleable** in a picker area whose tags come ONLY from `GET /research/taxonomy`; the Save affordance is present but **disabled with honest copy** (review saving lands with the review flow — mirror the approved Studies-disabled no-dead-link pattern);
  - unknown id ⇒ an explicit honest error state, never a blank page;
  - copy register: descriptive, thesis-attributed, "Descriptive only — not trading advice" discipline extends verbatim; no imperative or predictive wording.
- [ ] **`/journal` rows become links** to `/journal/[id]` (the iter-12 "deliberately not links" placeholder resolves now that the target exists).
- [ ] **Fold-in (coherence advisory):** replace the `▤` (U+25A4) glyph in the JournalTable empty state (`apps/frontend/components/JournalTable.tsx`) with text/class-based styling consistent with the design system.

### New user-facing capability
The user can open any journaled thesis and review it: what was expected vs what the tape actually did, what they actually did (marks), and what the machine-derived execution checks found — with mistake-tag suggestions pre-selected for the upcoming review flow.

### New information displayed
Per-thesis review detail: frozen statements + final statuses, the full verdict timeline with evidence at true clock time, frozen risk flags, action marks with spread-at-mark and realized R (when marked), execution checks with evidence, suggested mistake tags.

### New user actions
Click a journal row to open its detail; toggle suggested mistake tags in the (not-yet-savable) picker; navigate back to the list.

### UI surface changes
New `/journal/[id]` page under the Journal nav section; `/journal` table rows become links; JournalTable empty-state glyph cleanup.

### Product surface delta
The Review pillar becomes real: the journal stops being a list-only record and becomes an honest per-thesis review surface — the foundation J-56/J-57 (grades + review save) build on next iteration.

### Blueprint conformance
`/journal/[id]` lives under the existing **Journal** home exactly where the approved IA places it (`/journal` → `/journal/[id]`; J-54's home is listed there already). Reached in 2 clicks from the persistent nav (Journal → row). No nav-skeleton change; no reapproval needed.

### Data-contract additions
No new contract row. **Row 19's execution-checks half ships** (registered in `blueprint.md` as an iter-13 additive note): the four named checks + suggested tags are computed ONCE at terminal resolution by ONE backend function from recorded marks + the append-only timeline + frozen thesis fields only, persisted (schema v5), and served VERBATIM only by the already-registered `GET /research/journal/{id}`. **Row 24** gains the mistake-tag catalog (backend-owned labels + display copy via `GET /research/taxonomy`). The page reads statements, timeline, flags, and marks from their already-registered canonical sources — no second computation or serving path for any registered value.

## OUT OF SCOPE

- J-56 outcome × process grades (grade keys stay honestly absent from rows and detail).
- J-57 review SAVE flow: `POST /research/thesis/{id}/review`, the `reviewed` flip, `other`-requires-note validation — iter-14. This iteration only renders suggestions pre-selected + toggleable with a disabled Save.
- J-58 excursions, J-59 analytics, J-60–J-62 studies, all cues (J-53, J-63–J-67 — binding build order).
- Any engine / classifier / provider / chart-computation change (research stays observer-only; engine outputs byte-identical).
- Any change to `verdict_events` write semantics (append-only repository surface unchanged).
- The "re-watch this window" affordance on the detail page (goal.md mentions it for `/journal/[id]`; it is not part of J-54/J-55 acceptance — defer to a later journal-touching iteration to keep this lean).

## DEFINITION OF DONE

- [ ] Target journeys J-54, J-55 pass via browser-qa-agent (evidence frames opened, below-the-fold content captured via scroll-into-view/full-page).
- [ ] Required-still-passing journeys J-01, J-02, J-42, J-49, J-50, J-51, J-52, J-68 remain green — including the carried-forward **J-49 firing-flag chip pixel capture** (see TESTING).
- [ ] No anti-goal violation introduced (journal integrity, no naked outputs, no recompute-at-read, no grades/scores, no imperative/predictive copy).
- [ ] Unit tests pass; no regressions (backend suite green; migration test against a committed v4 fixture green).
- [ ] Blueprint row-19/row-24 additive notes match what shipped.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-13-dev.md`.

## TESTING REQUIREMENTS

- Browser (browser-qa-agent; diff the executed test list against this journey matrix before reporting):
  1. **J-54** (full flow on `SIM-REVERSAL`): declare **absorption_reversal / long** during the absorption phase; **mark an entry while the verdict is still `pending`**; let it confirm; mark an exit; resolve **Played out**; open `/journal/[id]`. Verify: `entered_before_confirmation` reads **failed** with evidence (entry timestamp < first confirming publish) and its mistake tag is **pre-selected and toggleable**; the chased / exited-beyond-invalidation / cut-confirming-early checks each show an enum status + evidence derived only from recorded marks + the timeline; no numeric score anywhere; the Save affordance is disabled with honest copy.
  2. **J-55**: open a resolved thesis with several transitions at `/journal/[id]` (the J-54 thesis or a fresh `SIM-BUYER` trend-continuation run). Verify: frozen statements with final statuses beside the timeline at true clock time, each transition carrying evidence; risk flags, action marks, and execution checks visible; capture the raw `GET /research/journal/{id}` payload in the same run and confirm the page renders those recorded values **verbatim** (REST detail = what is shown).
  3. **J-51/J-50 still green**: `/journal` list renders, rows are now links, filters still round-trip; empty-state glyph replaced.
  4. **J-49 fold-in (carried from iter-12)**: declare a thesis with a firing flag (e.g. `chasing_entry` on a long-extended `SIM-BUYER`) and capture ONE pixel frame of the class-based risk-flag chip on the strip.
  5. **J-01/J-02/J-42/J-52/J-68 spot-checks**: cockpit unchanged under the nav; declare→confirm→marks flow intact.
  - Mandatory practices (binding lessons): restart the QA backend after dev changes and run the **server-freshness canary** before any capture; `/journal/[id]` is a below-the-fold surface — use scroll-into-view/full-page captures; never `npm run build` against the live dev server's shared `.next` (use `NEXT_DIST_DIR=.next-qa`); any "untouched/no-regression" claim must be re-diffed against `changed_files`; budget-continued runs must re-verify that diff.
- Unit/integration (backend):
  - Each of the four checks: deterministic fixture timelines + marks driving failed / passed / `not_applicable` (no marks) outcomes, with evidence strings asserting the measured values; chase check anchored at `rule_first_true_price`, not the publish price.
  - Checks computed exactly once at resolution and persisted: resolve → read detail twice → byte-identical `execution_checks`; a pre-v5 resolved thesis (committed v4 fixture) serves the key ABSENT after migration — never backfilled.
  - Schema v5 migration test against the committed v4 fixture DB (versioned bump, ALTER in one writer transaction, existing rows untouched).
  - `GET /research/journal/{id}`: additive keys present post-resolution, absent pre-resolution; 404 unknown id unchanged; timeline rows byte-identical to pre-iteration shape (additive-only).
  - Taxonomy: mistake-tag catalog served by `GET /research/taxonomy` with display copy; frontend hardcodes none (review existing pattern).
- Error cases:
  - Unknown thesis id at `/journal/[id]` → explicit honest error state (page) and 404 (REST).
  - Thesis with no marks → mark-dependent checks `not_applicable` with honest copy; no realized-R shown.
  - Pre-migration resolved thesis → `execution_checks` key absent → "not assessed" honest copy, never invented checks.

## NOTES

- **Evaluator mandate (iter-12):** this is the recommended J-54+J-55 pair, lean, with the two fold-ins (J-49 firing-flag pixel, `▤` glyph) included. Depth lean also because the engine halts at `qa_complete` for FULL iterations (open harness defect).
- **J-54 scope boundary:** the "user confirms" save of suggested tags belongs to the J-57 review flow (iter-14 per the evaluator's binding build order). This iteration must demonstrate the suggestions **pre-selected and editable** with the system never tagging on its own; the disabled-Save-with-honest-copy pattern mirrors the approved Studies-disabled nav entry (no dead controls). If the evaluator judges the save clause necessary for a full J-54 pass, J-54 lands partial this iteration and completes with J-57 — do not pull the save flow forward.
- **Lessons applied (binding):** execution checks computed ONCE at resolution and persisted, ONE owner, no recomputation at read; store.py schema change ⇒ versioned migration + committed-fixture test (iter-4 lesson); new below-the-fold page ⇒ full-page/scroll-into-view captures and evaluator-opened PNGs; server-freshness canary after dev; `NEXT_DIST_DIR=.next-qa`; re-diff "untouched" claims against `changed_files`; reuse prior risk-flag/verdict frames only for re-rendered frozen data — the NEW detail surface needs fresh pixels.
- **Honest-omission pattern:** follows the established `risk_flags` precedent — key absent = never computed (pre-migration), present = computed at the defining moment. Never an empty-list lie, never backfill of historical rows.
- **Where checks are computed:** every terminal-resolution path calls the one function (user resolve, invalidation auto-resolve, stream-end expiry, restart-expiry sweep). If a path genuinely cannot supply the inputs, the key stays honestly absent for that thesis — it is NEVER computed lazily at read time.
