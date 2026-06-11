# Goal Iteration 14 — Complete the review pillar: grades (J-56), review save flow (J-57), final statement statuses (J-55)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 14
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-55, J-56, J-57
- **Required-still-passing journeys:** J-01, J-08, J-35, J-50, J-51, J-52, J-54, J-68
- **Anti-goal reminders:**
  - "**Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*"
  - "**No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect. *(critical)*"
  - "**No profitability or edge claims.** No currency P&L, equity curves, compounding, or win-rate-as-edge presentation anywhere. R statistics are journaled measurements and MUST always appear with their n, the abandonment bucket, the null baseline (where one applies), and the spread/R cost figure. *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect. *(critical)*"
  - "**Persistence stays scoped to research records.** SQLite holds theses, verdict events, hints, actions, reviews, and study results only — no trades, quotes, candles, or feature series are persisted (committed test fixtures excepted)."

## GOAL

A resolved thesis can be honestly reviewed end-to-end: its frozen expected-behaviour statements show their persisted FINAL statuses, its outcome × process grades render as enum labels in the quadrant and journal rows, and the user can confirm mistake tags + a note via an enabled Save that flips the thesis to `reviewed`.

## BACKGROUND

This is the iter-13 evaluator's mandated next step (verdict CONTINUE, depth lean): finish the review pillar before the evidence layer. Iter-13 shipped the `/journal/[id]` detail page, execution checks computed once at all four terminal-resolution paths (`compute_and_persist_execution_checks` in `app/research/execution_checks.py`, called from `routes.py` resolve + startup sweep and `monitor.py` invalidation + expiry), the full mistake-tag catalog in `GET /research/taxonomy`, and a deliberately disabled Save. Three gaps remain: J-55 is PARTIAL solely on the "statements listed with their final statuses" clause (statement statuses are LIVE-only in the monitor projection — `_evaluate_statement` in `monitor.py` — and persisted nowhere); J-56 grades are honestly absent; J-57's save flow (`POST /research/thesis/{id}/review`) does not exist. All three land at the SAME terminal-resolution/persist-once seam iter-13 proved, plus one small review endpoint — a lean, single-pillar iteration. Binding session lesson: any value a review surface must show "frozen" MUST be persisted at its defining moment, never recomputed at read.

## IN SCOPE

### Backend

- [ ] **Per-statement FINAL statuses (J-55 completion).** At every terminal resolution (the same four call sites as execution checks: user resolve, invalidation auto-resolve, stream-end expiry, restart-expiry sweep), persist each frozen statement's final status ONCE on the thesis — an additive field (e.g. a `statement_final_statuses` JSON column); NEVER mutate the frozen `statements` JSON itself. For live-monitored paths the final status is the monitor's last evaluated status at the terminal moment (or an at-resolution one-shot derivation from recorded evidence — computed once, at the defining moment). Where no live evaluation context exists at the terminal moment (e.g. restart-expiry sweep), record an explicit honest `unknown`/`not_evaluated` enum — never fabricated, never recomputed at read. Pre-migration resolved theses carry the key ABSENT (honest omission, never backfilled). Served verbatim only by `GET /research/journal/{id}`.
- [ ] **Outcome × process grades (J-56).** Computed ONCE at the same terminal-resolution seam (alongside execution checks), persisted, served verbatim by `GET /research/journal/{id}` and as additive keys on the `GET /research/journal` rows. Outcome `thesis_held | thesis_failed | no_read` is 1:1 from the resolution (per goal.md capability 29); process `clean | flagged | violated` is a **config-owned rule** over the named, evidence-backed checks (frozen entry risk flags + persisted execution checks) — enum labels with plain-language evidence naming which checks drove the grade, NEVER a numeric score. **Being invalidated is never by itself a process failure** (the system enforces invalidation). No new thresholds outside config. Display copy for grade labels comes from the row-24 taxonomy endpoint (frontend hardcodes none).
- [ ] **Review save flow (J-57).** `POST /research/thesis/{id}/review` with body `{mistake_tags, note?}`: tags validated against the backend taxonomy (unknown tag → 422); `other` requires the note (422 without); 409 unless the thesis is resolved; 409 if already reviewed (conservative immutability default — see NOTES); on success persists tags + note verbatim and flips the thesis to `reviewed`. The saved review and reviewed status are served by `GET /research/journal/{id}`; the `reviewed` flag lands as the pre-registered additive key on `GET /research/journal` rows. The append-only `verdict_events` write surface is untouched.
- [ ] **Schema v5 → v6 versioned migration** covering ALL additive columns this iteration (final statement statuses, grades, review tags/note/reviewed) in one bump: in-place `ALTER` in one writer transaction, never backfilling; proven by a test against a **committed v5 fixture** plus the persistent-DB check (session lesson — `CREATE TABLE IF NOT EXISTS` alone is never a migration).

### Frontend

- [ ] `/journal/[id]`: render each frozen statement with its persisted FINAL status badge (remove the iter-13 "see timeline" deferral note); statuses come verbatim from the detail payload — the page derives nothing, and pre-v6 rows render the honest absent state.
- [ ] `/journal/[id]`: render the **outcome × process quadrant** (two enum labels + the evidence naming the checks that drove the process grade), using taxonomy display copy.
- [ ] `/journal/[id]`: enable **Save review** — tags pre-selected from suggestions remain toggleable; selecting `other` requires the note (inline validation, honest copy); save calls the new endpoint; on success the saved tags + note + `reviewed` status render (and the system-suggested tags remain visible as suggestions, distinct from the user-confirmed tags).
- [ ] `/journal` list: additive **grades** and **reviewed** columns on rows (honest `—` omission for pre-grade/unreviewed rows), labels from taxonomy.

### New user-facing capability
The user can complete an honest review of any resolved thesis: see how each expected-behaviour statement finally resolved, read the two-axis grade ("disciplined thesis, adverse tape" vs "got away with it"), and confirm mistake tags + a note that flip the thesis to reviewed.

### New information displayed
Per-statement final status badges; outcome grade (`thesis_held | thesis_failed | no_read`); process grade (`clean | flagged | violated`) with check-naming evidence; saved mistake tags + note; reviewed status — on `/journal/[id]` and (grades/reviewed) on `/journal` rows.

### New user actions
The Save-review button (previously disabled) on `/journal/[id]`; the required-note input when `other` is selected.

### UI surface changes
`/journal/[id]` gains final-status badges, the quadrant block, and the live Save flow; `/journal` gains grade/reviewed row columns. No new routes, no nav change.

### Product surface delta
The review pillar (goal.md pillar 4) becomes fully usable: declare → judge → resolve → review now closes the loop, with J-54's "the user confirms" clause finally exercisable.

### Blueprint conformance
No new surfaces. All work lives at the already-approved Journal home: `/journal` and `/journal/[id]` (blueprint IA, Journal section; J-51/J-55–J-57 rows). The iter-13 disabled-Save placeholder resolves exactly as the blueprint's iter-13 note planned.

### Data-contract additions
- **Row 19 (additive note, registered):** the grades half ships (outcome 1:1 from resolution; process from config-owned rule over named checks) and **per-statement final statuses** persist at the same terminal-resolution moment — both computed once, persisted (schema v6), served verbatim only by `GET /research/journal/{id}`.
- **Row 21 (additive note, registered):** the pre-announced `grades` + `reviewed` additive row keys ship on `GET /research/journal`.
- **New row 28 (registered):** **Saved review** (user-confirmed mistake tags + note + reviewed flip) — computed/recorded once by `POST /research/thesis/{id}/review`, persisted, served by `GET /research/journal/{id}` (+ `reviewed` on row 21 rows). Tag/grade display copy stays owned by row 24 taxonomy.
- No second computation or serving path for any existing value: final statuses/grades/review are read ONLY from `GET /research/journal/{id}`; suggested tags (row 19) stay distinct from confirmed tags (row 28).

## OUT OF SCOPE

- Excursion outcomes (J-58), analytics aggregates (J-59), replay studies (J-60–J-62) — the evidence layer comes next, per the binding build order.
- ALL cue-layer work (J-53 management stance, J-63–J-67 checklist/stance/hints/feed badges) — strictly last, gated on the evidence layer (anti-goal: Evidence before cues).
- The "re-watch this window" affordance on `/journal/[id]` (lands later).
- Any engine/classifier/provider/chart change (J-68 sentinel: byte-identical engine outputs).
- Editing or backfilling any append-only timeline row or any frozen thesis field; no recompute-at-read anywhere.
- Hint log surface on `/journal` (lands with J-65).

## DEFINITION OF DONE

- [ ] J-55 passes via browser-qa-agent: statements listed WITH their final statuses beside the true-clock timeline; REST detail == UI verbatim; nothing recomputed at read.
- [ ] J-56 passes via browser-qa-agent: both acceptance quadrants produced and read in the journal — (1) SIM-SHIFT clean-process invalidated → `thesis_failed` × `clean`; (2) flagged-process played-out → `thesis_held` × `flagged`; enum labels only, evidence-backed, invalidation never itself a process failure.
- [ ] J-57 passes via browser-qa-agent: picker lists exactly the backend taxonomy; `other` requires the note; save persists tags + note, flips to `reviewed`; tags render identically everywhere they appear.
- [ ] Required-still-passing journeys remain green (J-01, J-08, J-35, J-50, J-51, J-52, J-54, J-68 sentinel).
- [ ] No anti-goal violation introduced (notably: journal integrity, no naked outputs, no numeric scores).
- [ ] Backend suite green including: v5→v6 migration against the committed v5 fixture, persistence at all four terminal paths, review-endpoint validation matrix; frontend builds (use `NEXT_DIST_DIR=.next-qa`, never the live dev server's `.next`).
- [ ] Blueprint Data Contract rows 19/21/28 match what shipped.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-14-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):**
  - **J-55** — open a resolved thesis with transitions (e.g. the J-56 runs); verify statements render WITH final-status badges; capture the raw `GET /research/journal/{id}` payload in the same run and assert REST == UI verbatim.
  - **J-56** — leg 1: SIM-SHIFT, declare trend_continuation/long early in the warm control phase (no flags), invalidation under the chop band, let it invalidate → read `thesis_failed` × `clean`. Leg 2: SIM-BUYER, produce a genuinely-firing risk flag at declaration (chase by declaring well into the extended move; iter-13 measured the impact return at ~0.0035 vs the 0.004 threshold, so declare later — or use the deterministic, pixel-proven `invalidation_too_tight` flag as the flagged-process vehicle), let it confirm, mark nothing or as needed, resolve Played out → read `thesis_held` × `flagged`. Verify the flag chip actually fired BEFORE resolving, or the leg is invalid.
  - **J-54 (regression on the same surface)** — checks still render with evidence; suggestions pre-selected/toggleable; now confirmable via Save.
  - **J-57** — on a resolved thesis: select tags including `other` → Save blocked/invalid without a note (honest inline copy); add the note → save succeeds; `reviewed` renders on detail AND on the `/journal` row; re-open the detail and verify persisted tags + note render from REST.
  - Below-the-fold `/journal/[id]` content: capture scroll-into-view/full-page PNGs — the evaluator opens pixels.
  - Mandatory pre-capture server-freshness canary: restart the QA backend after dev changes before any capture.
- **Unit/integration:**
  - Grade computation: outcome mapping 1:1 from each of the four resolutions; process rule over flags+checks from config (clean/flagged/violated cases); explicit test that an invalidated, no-flag, clean-checks thesis grades `clean`.
  - Final statement statuses persisted at ALL FOUR terminal paths; sweep/no-monitor path records the explicit `unknown`/`not_evaluated` enum; pre-v6 rows serve the key ABSENT.
  - Review endpoint: 422 unknown tag; 422 `other` without note; 409 unresolved; 409 already reviewed; success persists verbatim + flips `reviewed`; `verdict_events` untouched.
  - v5→v6 migration against the committed v5 fixture + freshly-created-store version stamp + persistent-DB check.
  - Journal rows: grades/reviewed keys present post-resolution/review, honestly absent before.
- **Error cases:** unknown thesis id on review → 404; malformed body → 422; no grade/status key ever fabricated for pre-v6 rows; UI renders honest omission, never a default value.

## NOTES

- **Evaluator mandate (iter-13, CONTINUE/lean):** this exact trio; "do not render statuses by re-deriving from the timeline at read time." Deriving once AT resolution from recorded evidence is acceptable; re-deriving at read is not.
- **Binding lessons applied:** persist-at-defining-moment (statement statuses are live-only today); versioned migration + committed old-schema fixture + persistent-DB check for any `store.py` schema change; single owner per served value, REST==UI verbatim; scroll-into-view captures for below-the-fold detail content; pre-capture server-freshness canary (restart QA backend after dev); budget-continued browser-qa runs must re-diff "untouched/no-regression" claims against changed_files; diff the executed browser test list against this spec's journey matrix; `NEXT_DIST_DIR=.next-qa` for any frontend build while the harness dev server runs.
- **Depth is lean deliberately:** the FULL-pipeline harness defect at `qa_complete` remains open upstream — stay lean until fixed. Scope crosses backend+frontend but rides a proven seam with one new endpoint; iter-13 shipped the same shape successfully as lean.
- **409-on-already-reviewed** is a conservative default chosen here because goal.md is silent on re-review; it keeps review records immutable in the spirit of journal integrity. If the developer finds a strong reason to allow an explicit re-review update instead, it must be honest, tested, and must never touch the append-only timeline — and the handoff must record the decision.
- **Suggested vs confirmed tags stay distinct:** `suggested_mistake_tags` (row 19, machine) are never auto-recorded as the review; only the user's Save records confirmed tags (row 28). The system never tags on its own.
- Grade and status display copy must come from `GET /research/taxonomy` (row 24) — the frontend hardcodes no labels; extend the taxonomy payload additively if grade/status enums need display copy.
- All review-surface copy stays past-tense, descriptive, thesis-attributed; the "Descriptive only — not trading advice" footer discipline extends to the new blocks. No numeric score appears anywhere.
