# Goal Iteration 15 — Evidence layer begins: excursion outcomes (J-58)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 15
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-58
- **Required-still-passing journeys:** J-01, J-08, J-42, J-50, J-51, J-52, J-54, J-55, J-56, J-57, J-68
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*
  - **No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect. *(critical)*
  - **No profitability or edge claims.** No currency P&L, equity curves, compounding, or win-rate-as-edge presentation anywhere. R statistics are journaled measurements and MUST always appear with their n, the abandonment bucket, the null baseline (where one applies), and the spread/R cost figure. *(critical)*
  - **No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*
  - **The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*
  - **Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect. *(critical)*
  - **Source, feed, and config honesty.** Every research record MUST be stamped with its bound source, its `data_feed`, and a `config_fingerprint` over the entire frozen config; a thesis MUST never be evaluated against a different source than it was declared on; analytics and studies MUST NOT pool across feeds or fingerprints; and SIP-derived research MUST NOT be presented as validating IEX-live behaviour without the explicit basis label. *(critical)*
  - **Persistence stays scoped to research records.** SQLite holds theses, verdict events, hints, actions, reviews, and study results only — no trades, quotes, candles, or feature series are persisted (committed test fixtures excepted).

## GOAL

A resolved-or-ended thesis on `/journal/[id]` shows honest, deterministic **excursion outcomes**: max favorable / max adverse excursion in **R units** per configured horizon, anchored at the **first published confirmation** AND separately at the **entry mark** (two populations, never pooled), each with the ternary outcome `+1R_first | −1R_first | neither_within_horizon`, spread-at-anchor beside it, and explicit **truncated** flags where the stream end or a gap cut a horizon short.

## BACKGROUND

The review pillar completed in iter-14 (J-55/J-56/J-57 all pixel-verified passing, COHERENCE-PASS). The binding build order now mandates the **evidence layer** (J-58–J-62) before any cue (J-53, J-63–J-67) — the *Evidence before cues* anti-goal. The iter-14 evaluator's primary recommendation is **J-58 alone at lean depth**: all anchors already exist (action marks + `spread_at_mark` since iter-8, timeline gap events since iter-9, `rule_first_true` + `last` on every published timeline event), and the work rides the persist-once terminal-resolution seam now proven three times (execution checks, final statuses, grades). J-59 (analytics) is deliberately deferred to keep this iteration lean-sized — it aggregates exactly the rows this iteration persists.

Binding lessons that shaped this spec (state/lessons.md): persist any "frozen" evidence value at its **defining moment**, never recompute at read; the **two excursion populations must never be pooled**; `store.py` schema changes require a versioned migration + a committed old-schema fixture + a persistent-DB check; single owner per served value with REST == UI verbatim; depth stays lean because the FULL pipeline's `qa_complete` harness defect remains open upstream.

## IN SCOPE

### Backend

- [ ] **Config — excursion research defaults** (`apps/backend/app/config.py`): add `excursion_horizons_seconds` (an ordered list of logical-time horizons) plus any other excursion constant the implementation needs, as documented **research defaults** calibrated against the seeded sims — no literal in research code. Choose defaults so the deterministic J-58 script (J-42's `SIM-BUYER` run to scenario end) exercises **both** at least one completed horizon and at least one stream-end-truncated horizon, and document that calibration. These values enter `config_fingerprint` (it spans the entire config dataclass — see NOTES).
- [ ] **Single-owner excursion calculator** — new module `apps/backend/app/research/excursions.py`. An in-memory tracker, fed only by the existing research-monitor observer (read-only over the engine), that:
  - arms the **confirmation-anchored** population once, at the **first published `confirming`** timeline event (reference price = the `last` recorded on that published event — already persisted on the append-only timeline; document this basis). Re-confirmation after weakening never re-arms;
  - arms the **entry-anchored** population once, at the recorded **entry mark** (reference price = the verbatim mark price; spread-at-mark already stamped by row 18 — reuse it, never re-stamp);
  - captures **spread-at-anchor once at the arming moment** from the current snapshot for the confirmation population (a moment value, like row 18's `spread_at_mark` — never recomputed);
  - uses **R = |reference − invalidation|** via the **same single R-basis helper row 27 uses** — one shared function, never a second formula;
  - tracks running MFE/MAE in R per population and resolves the **ternary outcome per horizon by first touch** (+1R reached first vs −1R reached first vs neither within the horizon) in **logical time**;
  - **truncates** any open horizon at stream end or at a gap event (`paused` teardown, `watch_restarted`, stale span — the row-16 gap events), flagging it `truncated` — a horizon is never bridged across a gap and never extrapolated;
  - keeps the two populations fully segregated end to end — separate anchors, separate R bases, separate per-horizon rows; nothing ever pooled or averaged across them.
- [ ] **Persist once** — `compute_and_persist_excursions(...)` following the proven seam: persisted via the single writer queue at the four terminal paths (user resolve, invalidation auto-resolve, stream-end expiry, restart-expiry sweep) **and** at the stream-end survival path for an entry-marked thesis that survives as active-but-not-evaluated (J-58's script ends exactly there — the record must exist without a resolution). Once persisted, values are frozen — never recomputed at read, never reopened on a matching-source re-attach. Where tracker state is unavailable at the persist moment (e.g. the restart-expiry sweep after a backend restart), persist an explicit honest not-tracked marker — never fabricated numbers, never a dishonest zero.
- [ ] **Schema v6 → v7** (`apps/backend/app/research/store.py`): one additive column on `theses` for the excursion record; versioned migration step (in one writer transaction, no backfill of pre-v7 rows); a **committed v6 fixture** proving the migration; a **persistent-DB check** (restart → served values byte-identical, proving no read-time recomputation). Pre-v7 resolved theses carry the key **ABSENT** (honest omission, the iter-13/14 pattern).
- [ ] **Serve verbatim, one endpoint**: the persisted excursion record is served ONLY by the existing `GET /research/journal/{id}` (`build_journal_detail`) — no new endpoint, no second serving path, no client-side arithmetic.
- [ ] **Taxonomy (additive)**: ternary-outcome labels, the `truncated` label, the not-tracked / not-applicable copy, and the two population display titles ship via `taxonomy_payload()` (`GET /research/taxonomy`) — the frontend hardcodes none of them.

### Frontend

- [ ] **Excursion section on `/journal/[id]`** (`JournalDetailView.tsx`, under the existing execution-checks/grades area): two **visually separate** blocks — "From first confirmation" and "From entry mark" — each showing its anchor (true-clock time, mono reference price, spread-at-anchor, R basis) and per-horizon rows: horizon, MFE (R), MAE (R), the ternary outcome chip, and a TRUNCATED flag where set. Never-confirmed ⇒ the confirmation block reads an explicit not-applicable; no entry mark ⇒ the entry block reads an explicit not-applicable (no mark, no metric — no dishonest zero). Pre-v7 rows render the honest-omission copy (same register as iter-14's pre-v6 treatment). Copy is descriptive, past-tense, R-units only — no currency, no prediction.
- [ ] **Carry-along cleanup (coherence advisory)**: unify the grade-chip emerald shade between `JournalDetailView.tsx` (`bg-emerald-900/40`) and `JournalTable.tsx` (`bg-emerald-900/20`) — one shade for the same grade id on both surfaces.

### New user-facing capability
After a thesis runs its course, the user can read — per horizon — how far the tape actually went for and against the idea in R units, separately from the moment the tape confirmed it and from the moment they actually entered, with the spread cost recorded beside it and truncation declared instead of hidden.

### New information displayed
MFE/MAE in R per configured horizon; ternary `+1R_first | −1R_first | neither_within_horizon` outcome chips; spread-at-anchor per population; TRUNCATED flags; anchor details (time, reference price, R basis) for each of the two populations.

### New user actions
None — this iteration is read-only display of machine-measured evidence (no new buttons or forms).

### UI surface changes
One new excursion section on `/journal/[id]`; a one-line shade unification on the existing grade chips. No new pages, no nav change.

### Product surface delta
The journal detail page becomes the first surface of the **evidence layer**: review is no longer just verdicts + grades but measured post-confirmation and post-entry outcomes — the substrate J-59 analytics and J-60 studies will aggregate.

### Blueprint conformance
No new routes. The excursion section lives on `/journal/[id]` under the **Journal** home — already registered in the blueprint IA ("J-54, J-58 (execution checks, excursions) → `/journal/[id]` → Journal"). Blueprint updated with an iter-15 build-out note (additive; no skeleton change, no reapproval needed).

### Data-contract additions
No new contract row — row 20 (**Excursion outcomes**) was pre-registered and is now built out (single owner `app/research/excursions.py`; served only by `GET /research/journal/{id}`). Row 24 gains additive excursion display copy. The R basis REUSES row 27's single computed basis via one shared helper — never a second formula. Registered in `blueprint.md` (rows 20 and 24 build-out notes).

## OUT OF SCOPE

- **J-59 analytics** (`GET /research/analytics` + the `/journal` analytics view) — next iteration; it aggregates only the rows this iteration persists.
- **J-60–J-62 replay studies** and the `/studies` page beyond the existing disabled-entry state.
- **All cue-layer work** (J-53 management stance, J-63–J-67 checklist/stance/hints/copy/feed-label journeys) — binding build order: cues strictly after J-58–J-62 pass.
- Any engine / classifier / feature / provider / chart change — the diff must stay research/journal-scoped (J-68 sentinel).
- Any change to how row 18 marks, row 16 timelines, row 19 checks/grades, or row 27 realized-R are computed or served.
- Backfilling excursions for pre-v7 (or already-resolved pre-iter-15) theses — honest omission only.

## DEFINITION OF DONE

- [ ] Target journey **J-58** passes via browser-qa-agent against its goal.md acceptance clauses (two segregated populations, R units, ternary per horizon, spread-at-mark recorded, truncation flagged, seeded re-run reproduces identical numbers)
- [ ] Required-still-passing journeys J-01, J-08, J-42, J-50, J-51, J-52, J-54, J-55, J-56, J-57, J-68 remain green
- [ ] No anti-goal violation introduced (journal integrity, no naked outputs, no P&L/edge claims, read-only research layer, evidence-before-cues untouched)
- [ ] Unit tests pass; backend suite green; no regressions; no engine file in the diff
- [ ] Schema v7 migration proven against the committed v6 fixture; persistent-DB check proves no read-time recomputation
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-15-dev.md`

## TESTING REQUIREMENTS

- **Browser (J-58 script, per goal.md):** watch `SIM-BUYER` (Simulated), declare **trend_continuation / long** with an invalidation below (the J-42 substrate), wait for the published `confirming`, record an **entry mark**, let the scenario run to its end (the entry-marked thesis survives as active-but-not-evaluated), open `/journal/[id]`, and verify: both population blocks render with distinct anchors and distinct numbers; every figure is in R; each horizon row carries its ternary outcome; spread-at-anchor shows on both blocks; at least one horizon reads TRUNCATED at the stream end; no currency symbol anywhere. Also verify a **no-entry-mark** thesis shows the entry block's explicit not-applicable, and a **pre-v7** resolved thesis renders the honest-omission copy. Re-verify the required-still-passing list on the same surfaces (J-54/J-55/J-56/J-57 sections still render on the same page; J-52 marks unchanged; J-51 restart persistence; J-50 journal rows; J-42 confirming flow; J-68 no-thesis cockpit sentinel; J-01/J-08 cockpit + REST==UI).
- **Unit/integration:**
  - determinism — running the identical seeded scenario + declaration + mark sequence twice yields **byte-identical** persisted excursion records (J-58's explicit unit-test clause);
  - first-touch ordering — a synthetic price path crossing −1R then +1R inside one horizon resolves `−1R_first`;
  - truncation — stream end and a gap event each truncate open horizons with the flag set; nothing extrapolated, nothing bridged across a gap;
  - segregation — confirmation- and entry-anchored records hold independent anchors/R bases and are never merged in the persisted record or the served projection;
  - honest absence — never-confirmed ⇒ no confirmation population; no marks ⇒ no entry population; tracker-unavailable persist paths record the explicit not-tracked marker;
  - migration — v6 fixture migrates to v7 in one transaction with pre-v7 rows untouched (key ABSENT); persistent-DB restart check serves byte-identical values (no read-time recomputation);
  - equivalence — the existing engine byte-identical-with-observers test still passes; no engine/classifier/provider/chart file changed.
- **Error cases:** no new write endpoints this iteration; existing validation matrices (404/409/422 on thesis/action/resolve/review) must be unaffected — spot-check via the existing tests.
- **QA process requirements (binding lessons):** restart the QA backend after dev and run the server-freshness canary before any capture; below-the-fold `/journal/[id]` content needs scroll-into-view or full-page captures (the evaluator opens the PNGs); **validate every cited capture is non-blank** (sanity-check file size / non-uniform pixels) before citing it; on a budget-continued run, re-diff any "untouched/no-regression" claim against `changed_files`; diff the executed browser test list against this spec's journey matrix; never `npm run build` against the live dev server's shared `.next` (use `NEXT_DIST_DIR=.next-qa`).

## NOTES

- **Depth is lean by mandate:** the FULL pipeline's `qa_complete` harness defect remains open upstream; the iter-14 evaluator explicitly recommended lean. The work is one new backend module + one schema bump + one page section, riding a 3x-proven seam.
- **Config-fingerprint shift is expected:** adding `excursion_horizons_seconds` to the config dataclass changes `config_fingerprint` for all records created after this iteration. That is the intended honesty mechanism (analytics never pools across fingerprints) — the evaluator should not read the stamp change as a defect. Document the new values as research defaults with their sim calibration.
- **Why the stream-end survival path persists:** J-58's script ends the scenario with an entry-marked thesis, which survives active-but-not-evaluated (capability 24). The excursion record's defining moment is the stream end (truncation), so it must persist there even though no resolution occurs — the journal detail must render excursions for that surviving thesis.
- **Single-owner discipline:** reference prices come from already-persisted facts (the timeline event's `last`, the mark's verbatim price); spread-at-entry reuses row 18's stamped `spread_at_mark`; the R basis reuses row 27's single helper. The only new moment value is spread-at-confirmation-anchor, stamped once at arming — mirror row 18's pattern.
- **Evaluator feedback applied:** iter-14 eval.md Next-Step Recommendation followed verbatim (primary target J-58; J-59 deferred as it does not fit lean alongside the schema + tracker work); both carry-along cleanups (emerald shade, non-blank capture validation) folded in.
