# Goal Iteration 19 — Browser-verification pass: `/studies` pixels flip J-60/J-61; J-68 sentinel re-capture (no new feature scope)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 19
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-60, J-61, J-68
  - J-60 and J-61 are partial ONLY on their UI/pixel legs — every backend clause is CI-proven and evaluator re-run (iter-18). This iteration exists to produce the missing rendered-pixel evidence.
  - J-68 is targeted for **partial-clause reduction only** (the pixel sentinel was not re-run in iter-18; the only intended cockpit-adjacent change is the enabled Studies nav entry). It is NOT expected to flip — its "J-01–J-37 all green" clause debt remains out of scope here.
- **Required-still-passing journeys:** J-01, J-02, J-08, J-09, J-17, J-19, J-31, J-35, J-38, J-42, J-50, J-51, J-52, J-54, J-55, J-56, J-57, J-58, J-59, J-62 — plus every other journey currently `passing`/`already_passing` in journey-history.json.
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - "**No profitability or edge claims.** No currency P&L, equity curves, compounding, or win-rate-as-edge presentation anywhere. R statistics are journaled measurements and MUST always appear with their n, the abandonment bucket, the null baseline (where one applies), and the spread/R cost figure." *(critical)*
  - "**Source, feed, and config honesty.** Every research record MUST be stamped with its bound source, its `data_feed`, and a `config_fingerprint` over the entire frozen config; a thesis MUST never be evaluated against a different source than it was declared on; analytics and studies MUST NOT pool across feeds or fingerprints; and SIP-derived research MUST NOT be presented as validating IEX-live behaviour without the explicit basis label." *(critical)*
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested)." *(critical)*
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do." *(critical)*
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists." *(critical)*
  - "**No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey." *(critical)*
  - "**No scanning, no execution — still.** Theses and hints exist only on the one watched ticker; studies run only over explicitly chosen windows; there is no background or multi-symbol setup detection…"
  - "**No new indicators, no auto-tuning.** Confirmation rules, stances, hints, and studies MUST be composed from the EXISTING engine features and states only; research thresholds are config-owned research defaults calibrated against the sims/fixtures; no parameter optimizer, grid search, or automatic threshold fitting of any kind." *(critical)*

## GOAL

The already-shipped `/studies` surface is proven in rendered pixels — create/monitor/read a reference-window replay study with its seeded null baseline side-by-side, and every studies-honesty state (hindsight label, truncation, cancelled+partial, explicit failure) — flipping J-60 and J-61 to passing and re-capturing the J-68 cockpit sentinel.

## BACKGROUND

Iter-18 delivered the full replay-study layer (capability 32): reviewer PASS, COHERENCE-PASS, full suite 671/1 green with zero re-pins, the pinned reference study byte-stable in CI (J-62 flipped on that automated evidence). But the QA production-build step corrupted the live dev server's shared `.next`, browser QA was SKIPPED 0/33, and the brand-new `/studies` page has **zero pixel evidence** — so J-60/J-61 advanced only to partial (the iter-2/3 rule: a UI journey cannot flip on a skipped browser run), and the J-68 pixel sentinel went un-captured. The evaluator's explicit recommendation is this lean browser-verification iteration. The human blueprint re-approval for the iter-18 nav-skeleton change (Studies entry enabled) has CLEARED — `state/blueprint.approved` is present (12-06-2026) and the `reapproval-requested` marker is gone; no gate blocks this iteration.

This is an evidence-completion iteration: **no new feature scope, no planned code change.** The code under test is the committed iter-18 work. When J-60/J-61 flip, the *Evidence before cues* gate (J-58–J-62 all passing) opens for the strictly-last cue layer (J-53, J-63–J-67) — which remains OUT of this iteration.

Lessons applied (state/lessons.md):
- **iter-18 / iter-2:** the pipeline ordering itself is the hazard — `npm run build` against the live dev server's shared `.next` destroys the browser-QA substrate. This iteration MUST NOT run a production build before browser QA completes (defer it, or isolate the dist dir); the browser-qa step must re-probe the frontend with a fresh canary before declaring any SKIP, and an all-SKIP browser report is "frontend unverified", never a pass.
- **iter-6:** start/restart both servers AFTER any code state is final and verify code identity with a canary probe BEFORE any capture — `GET /research/taxonomy` must carry the iter-18 studies copy (study status labels / `hindsight_level` label / null-baseline caption), and server start time must be newer than the newest patched file.
- **iter-2/3/14:** every cited capture must be full-page or scrolled-into-view, and non-blank (sanity-check file size / non-uniform pixels — three 6,303-byte blank frames have slipped through before). The evaluator opens pixels; filenames prove nothing.
- **iter-5:** diff the executed test plan against this spec's journey-leg matrix before execution — no silently dropped legs.
- **iter-1:** transient phases are time-critical — the unpaced PG-fixture study completes in ~10 s, so `queued`/`running`+progress frames must be captured promptly after create (and REST cross-checks carry the sequence claim if a phase is missed).
- **iter-16:** the persistent dev journal DB (`apps/backend/tapeology_journal.db` via `TAPEOLOGY_JOURNAL_DB`) already holds iter-18's API-created studies (including cancelled/failed records from QA TC-04/06/09/10) — stored results are persisted-once and served verbatim, so rendering those records is legitimate pixel evidence for states that are hard to time live.

## IN SCOPE

### Backend
- [ ] **None.** No backend code change is planned. The backend under test is the committed iter-18 code.

### Frontend
- [ ] **No planned code change.** Environment repair only: remove the corrupted `apps/frontend/.next` build dir (confirmed still present on disk at planning time) so the dev server starts clean (operational, not app code).
- [ ] **Conditional, tightly bounded:** ONLY if the browser run exposes a defect that blocks a J-60/J-61 acceptance clause, a minimal fix limited to the studies frontend surfaces (`apps/frontend/app/studies/`, studies components, `lib/api.ts`/`lib/types.ts` studies wiring) is permitted. NO backend logic change, NO engine/provider/classifier/store file, NO schema or config change, NO new endpoint. Any such fix must be named in the dev handoff with its triggering pixel evidence.

### New user-facing capability
None new — this iteration *proves* the iter-18 capability in pixels: the user can visibly create, monitor, cancel-read, and re-read deterministic replay studies with their seeded null baseline.

### New information displayed
None new (verification of the already-shipped `/studies` surface).

### New user actions
None new.

### UI surface changes
None planned (the `/studies` page and enabled Studies nav entry shipped in iter-18).

### Product surface delta
The evidence layer's last two journeys gain rendered-pixel proof, completing the Evidence-before-cues gate (J-58–J-62) and unlocking the cue layer for future iterations.

### Blueprint conformance
No new surfaces. All verified pages live at their registered homes: `/studies` (nav section **Studies**, registered row "J-60–J-62"), `/` (Cockpit), `/journal` (Journal). The iter-18 nav-skeleton change is already human-approved (`state/blueprint.approved`, 12-06-2026). No blueprint edit required this iteration.

### Data-contract additions
None. No new displayed value; all rendered values read verbatim from their registered owners/endpoints (row 23 study results via `GET /research/studies*`; row 24 taxonomy copy via `GET /research/taxonomy`). No second computation or serving path may be introduced.

## OUT OF SCOPE

- The cue layer: J-53 management stance, J-63 entry checklist, J-64 stance freshness, J-65 hints, J-66 copy sweep, J-67 feed labels — strictly last, next iterations.
- Any change to `app/engine/`, `app/providers/`, the classifier, history buffer, chart core, `store.py` schema, `config.py`, or any `/research` endpoint.
- Any new page, route, nav change, component library, or dependency.
- The long-tail J-01–J-37 partials (J-11/J-14/J-16/J-18/J-20/J-22/J-23/J-27/J-28/J-29/J-32, J-15) — they gate the J-68 full flip but are a separate, later effort.
- Re-pinning any test value; any analytics or journal change.
- Running `npm run build` into the live dev server's shared `.next` before browser QA completes.

## DEFINITION OF DONE

- [ ] Target journeys J-60 and J-61 pass via browser-qa-agent with evaluator-openable, non-blank, full-page (or scrolled-into-view) captures for every journey leg in TESTING REQUIREMENTS.
- [ ] The J-68 pixel sentinel is re-captured: the `/` cockpit with no thesis is unchanged except the enabled Studies nav entry.
- [ ] Required-still-passing journeys remain green (spot-checked in the same browser session: cockpit J-01/J-08, journal reachability).
- [ ] No anti-goal violation introduced (no code change expected; if a conditional frontend fix lands, the diff stays inside the permitted studies-frontend boundary).
- [ ] Backend suite still green (`cd apps/backend && .venv/bin/python -m pytest tests/` — exit code 0; expected unchanged from 671 passed / 1 skipped; verify by exit code, not an extra `-q`).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-dev.md` (documenting the environment repair, any conditional fix or explicitly "no code change", and the canary evidence).

## TESTING REQUIREMENTS

**Preconditions (mandatory, before ANY capture):**
1. Clear `apps/frontend/.next` (the corrupted dir is confirmed still on disk); start the frontend dev server fresh; start/restart the backend fresh.
2. Canary-probe both: `GET /health` 200; `GET /research/taxonomy` carries the iter-18 studies copy (study status labels, the `hindsight_level` label, the null-baseline caption); frontend serves `/studies` without a 500. Server start times must be newer than the newest committed file mtime.
3. Diff the executed test plan against this journey-leg matrix; the iter-18 designed plan at `reports/phase-goal-i_will_be_super_rich_with_my_loved_ones-iter-18-ui-test-plan.md` is the starting point (33 tests, never executed) — re-use it, do not redesign from scratch.
4. NO production build into the shared `.next` until all captures are complete.

**Browser — J-60 legs (each with non-blank, full-page evidence):**
- Navigate from `/` via the persistent nav's **Studies** entry (1 click) → `/studies` renders: create form, job list, the measurement-framing line ("Descriptive only…" register), copy from taxonomy.
- Create a study on the **committed reference window quick-pick** (PG SIP fixture, credential-free), setup `absorption_reversal` (or `trend_continuation`) × direction; capture the job status sequence — `queued`/`running` with progress (capture promptly; the unpaced run completes in ~10 s), then `done`. REST cross-check `GET /research/studies/{id}` alongside.
- Open results: occurrence rows (arm time, verdict summary, per-horizon ternary excursions), aggregates **side-by-side with the seeded random-arm-time null baseline** (the "setup: n/x `+1R_first`; random-time baseline: y/N" shape), `data_feed` + `config_fingerprint` stamps and the recorded seed visible, n + caveats, no edge claim anywhere. Expected pinned anchors (from the committed reference test): PG SIP setup n=2 / null n=99, occurrence `r_basis` [0.3, 0.6], verdicts [invalidated, confirming].
- Re-run the **identical** study; verify identical results in pixels plus a REST byte-equality cross-check of the two payload results.
- One **seeded sim source** leg (SIM-REVERSAL study): runs to `done` with results rendered (expected setup n=1, +1R at the 60/120 s horizons, null n=100).

**Browser — J-61 legs (each with non-blank evidence):**
- A `level_break` study with a manual level → results carry the visible **`hindsight_level`** label ("level chosen with hindsight — illustrative") and the cross-study-exclusion note.
- A level-setup study submitted WITHOUT a level → honest inline error from the backend 422 (never a guess, never a silent no-op).
- **Truncated** occurrences flagged and counted separately in pixels (the PG-window end truncates horizons — present in the reference results).
- A **cancelled** study rendered with explicit `cancelled` status and partial results clearly marked PARTIAL (never presented as complete). A live mid-run cancel is preferred; if job speed makes the live cancel un-capturable, rendering an existing cancelled record from the persistent dev DB (iter-18 QA created them via API) is acceptable pixel evidence — goal.md marks cancellation itself as "covered by a test".
- A **failed** study rendered with an explicit error — never an empty success (an existing failed record from the persistent dev DB is acceptable, same rationale).
- Job-list status badges + progress visible for at least two distinct statuses in one frame.

**Browser — J-68 sentinel + regression spot-checks:**
- Full-page `/` cockpit capture with no thesis: all J-01 panels populated on SIM-BUYER, unchanged except the enabled Studies nav entry; nav round-trip Cockpit → Journal → Studies → Cockpit.
- `/journal` loads with its rows/analytics view intact (reachability spot-check; no full re-run).

**Unit/integration:** no new tests required; the full backend suite must still exit 0 (re-run as a regression check, especially if any conditional frontend fix lands).

**Error cases:** the level-without-level 422 inline rendering (above); unknown-study-id `GET /research/studies/{id}` → honest 404 (REST probe).

## NOTES

- **This is the spec's central discipline:** the iteration ships pixels, not code. If browser QA cannot run (frontend dead again), the iteration must conclude as failed verification — never a soft PASS on skips (iter-2/iter-18 lessons). The browser-qa step must hard-flag a dead frontend, not soft-skip, because the target journeys are UI journeys.
- The known FULL-pipeline `qa_complete` harness halt is still open upstream — lean depth keeps this iteration inside the proven lean cycle (developer → reviewer → browser-qa).
- Blueprint status: re-approval for the iter-18 nav change is complete (`state/blueprint.approved` present, refreshed 12-06-2026; the `reapproval-requested` marker is gone); no blueprint edit or re-approval is needed for this iteration.
- This spec was re-derived after an infrastructure pause re-ran iteration 19's planning step; it supersedes the earlier identical draft — the plan is unchanged.
- Evaluator note: J-62 stays passing on its automated evidence; nothing here re-litigates it. J-60/J-61 flips should be judged on the pixel legs ONLY — their backend clauses were independently re-run and accepted in iter-18.
- After this iteration: if J-60/J-61 flip, the Evidence-before-cues door (J-58–J-62) is fully open; the recommended next target is the cue layer per the binding build order (J-53 management stance and/or J-63 entry checklist at the `/` thesis strip — blueprint row 25), with J-67's live feed-basis label as a candidate companion.
