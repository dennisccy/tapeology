# Goal Iteration 16 — Segregated journal analytics (J-59) + honest-absence copy split

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 16
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-59
- **Required-still-passing journeys:** J-01, J-08, J-50, J-51, J-52, J-54, J-55, J-56, J-57, J-58, J-68
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - "**No profitability or edge claims.** No currency P&L, equity curves, compounding, or win-rate-as-edge presentation anywhere. R statistics are journaled measurements and MUST always appear with their n, the abandonment bucket, the null baseline (where one applies), and the spread/R cost figure. *(critical)*"
  - "**Source, feed, and config honesty.** Every research record MUST be stamped with its bound source, its `data_feed`, and a `config_fingerprint` over the entire frozen config; a thesis MUST never be evaluated against a different source than it was declared on; analytics and studies MUST NOT pool across feeds or fingerprints; and SIP-derived research MUST NOT be presented as validating IEX-live behaviour without the explicit basis label. *(critical)*"
  - "**Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; … Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*"
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; … *(critical)*"

## GOAL

After this iteration the user can open the analytics view on `/journal` and read honest, segregated aggregates of their own journal — per setup × direction, partitioned by `data_feed` and `config_fingerprint`, with the abandonment bucket always visible and median spread/R beside every +1R figure — so the system's own helpfulness becomes inspectable from recorded evidence.

## BACKGROUND

Iter-15 shipped J-58 (excursion outcomes) and the evaluator confirmed every input J-59 needs is now persisted: grades, resolutions, saved review tags (row 28), and excursion records with per-population ternary outcomes plus feed/fingerprint stamps. The evaluator's recommendation for iter-16 is exactly this scope at lean depth: one read-only aggregation module + endpoint, one view on `/journal`. A ready-made never-pool browser assertion exists for free: iter-15's new excursion config keys intentionally shifted `config_fingerprint`, so pre- and post-iter-15 records MUST land in separate partitions on screen.

Carry-along (iter-15 evaluator finding 1 / iter-15 lesson): the single honest-absence fallback copy in `JournalDetailView.tsx` ("…and this thesis predates that", lines ~496/~573/~822) is factually wrong on a still-ACTIVE v7-era thesis. The absent key has two causes and must get two copies: "not yet resolved" vs "predates the feature".

Build order stays binding: studies (J-60–J-62) come next; cues (J-53, J-63–J-67) strictly last. Neither is touched here.

## IN SCOPE

### Backend

- [ ] **New single-owner analytics module** `apps/backend/app/research/analytics.py` — computes the J-59 aggregates from **persisted rows ONLY** (theses, verdict_events, actions, reviews/tags, and the persisted excursion records). It aggregates stored values; it NEVER recomputes any underlying canonical value (no re-derived verdicts, no second excursion math, no second R formula).
- [ ] **New endpoint `GET /research/analytics`** — the single serving path (blueprint row 21, aggregates half). Returns the full segregated projection; the frontend renders it verbatim.
- [ ] **Partitioning is structural, not optional:** the top-level response shape is keyed by (`data_feed`, `config_fingerprint`) partitions; within a partition, groups are per `setup_type` × `direction`. There is no "all" / pooled rollup anywhere in the payload. Each partition carries its feed label and fingerprint (short form ok for display, full value present).
- [ ] **Per group, the aggregates from goal.md J-59 / capability 31:**
  - `n` with the **abandonment bucket always visible** (count of `abandoned` rendered even when 0; abandoned theses stay in every denominator — no survivorship pruning),
  - the **ternary excursion distribution** per configured horizon from the **confirmation-anchored** population (counts of `+1R_first | −1R_first | neither_within_horizon`); **truncated** horizons are counted separately and visibly — never silently pooled into resolved buckets, never extrapolated,
  - **median time-to-confirm** (declaration → first published `confirming` timeline event, **logical time**, from the persisted append-only timeline; absent for groups with no confirmation — honest omission, not zero),
  - **tag frequencies** from saved reviews (row 28 user-confirmed tags only — machine SUGGESTIONS are never counted),
  - the **acted-trade R distribution** (entry+exit-marked theses) **kept structurally apart** from confirmation-anchored stats — distinct keys/blocks, never merged; realized-R values come from the row-27 projection function in `marks.py` (the one registered R path) over persisted marks — no second formula, no inline arithmetic,
  - **median spread/R** beside every +1R figure (median of persisted `spread_at_anchor / r_basis` for that population — the no-cost caveat as a number).
- [ ] **Insufficient-sample gating:** new config key (e.g. `analytics_min_sample_size`) as a documented **research default**; groups with n below it serve an explicit `insufficient_sample` marker with n still present — never bare percentages. This key is **serving/presentation-only** and is **excluded from `config_fingerprint`** with a documented rationale comment (iter-12 page-size precedent, `config.py` ~line 448: fingerprinting a display threshold would dishonestly fragment the pools); pin with a unit test that changing the key does NOT change the fingerprint.
- [ ] **Analytics display copy via taxonomy** (row 24): group/section titles, abandonment-bucket label, insufficient-sample copy, truncated label reuse, spread/R caption, and the "journaled measurements, not performance" framing line — served by `GET /research/taxonomy`; the frontend hardcodes none.
- [ ] **NO schema change:** analytics reads existing persisted rows; `store.py` stays at v7 — no migration this iteration.

### Frontend

- [ ] **Analytics view on `/journal`** (the blueprint-registered home — a view/tab within the existing Journal page; NO new route, NO new nav entry; the thesis table remains the default view so existing J-50/J-51 captures are unaffected). Renders the `GET /research/analytics` payload **verbatim** (display rounding only, no client-side arithmetic): partition blocks (feed + fingerprint stamps visible, pre- vs post-iter-15 fingerprints rendering as separate blocks), per setup × direction groups with n + always-visible abandonment bucket, ternary distribution chips with separate truncated counts, median time-to-confirm, tag frequencies, the acted-trade R block visually separate from the confirmation-anchored block, median spread/R beside every +1R figure, and the insufficient-sample state with n shown. All copy from taxonomy; dates (if any) via the one shared dd-MM-yyyy formatter; no equity curve, no currency, no win-rate-as-edge presentation anywhere.
- [ ] **Carry-along — honest-absence copy split** in `JournalDetailView.tsx` (grades ~496, excursions ~573, execution checks ~822): when the key is absent AND the thesis is unresolved → "not yet" copy (computed once the thesis resolves / runs its course); when absent AND resolved → "predates the feature" copy. Both strings from taxonomy if the existing fallbacks already source from it; otherwise match the established copy register.

### New user-facing capability

The user can review their accumulated journal as honest, segregated statistics for the first time — the question "do my setups measurably help?" gets its first recorded-evidence answer surface (pre-studies).

### New information displayed

Per-partition (feed × fingerprint), per setup × direction: n, abandonment count, ternary excursion distributions per horizon with truncated counts, median time-to-confirm, mistake-tag frequencies, acted-trade R distribution (separate), median spread/R beside +1R figures, insufficient-sample markers.

### New user actions

Switching `/journal` between the thesis-table view and the analytics view (one control). No other new actions.

### UI surface changes

`/journal` gains the analytics view (registered home). `/journal/[id]` gets the three-fallback copy split. Nothing else moves.

### Product surface delta

The Review pillar completes its analytics half (capability 31). The journal stops being only a record and becomes a measurement surface — the prerequisite framing for studies (J-60–J-62) next.

### Blueprint conformance

J-59's canonical home is pre-registered: "J-59 (segregated analytics) → `/journal` analytics view → Journal" (blueprint IA table). No new route, no nav-skeleton change, ≤2 clicks (Journal is one click; the view toggle is the second). The disabled Studies nav entry is untouched.

### Data-contract additions

No new contract row. Row 21's **aggregates half** ships exactly as registered: single owner `apps/backend/app/research/analytics.py`, served ONLY by `GET /research/analytics`, computed over persisted rows only, never pooled across `data_feed` or `config_fingerprint`. Acted-trade R reuses the row-27 projection (one R path, now three registered consumers of `r_basis`). Analytics display copy is additive on row 24. The blueprint has been updated with additive iter-16 notes registering this.

## OUT OF SCOPE

- Replay studies (J-60–J-62): no study runner, no `/studies` page enablement, no reference fixture, no CI timing gate.
- The entire cue layer (J-53, J-63–J-67): no stance, no checklist, no hints, no hint log view, no feed badge on the live cockpit.
- Any engine / classifier / provider / chart-core / feeder change — the diff must contain no such file (J-68 byte-identical equivalence stays green).
- Any `store.py` schema change or migration (none is needed; do not add one).
- Any new persisted value — analytics is read-time aggregation over already-persisted records.
- Any pooled / "all feeds" / "all configs" rollup, any percentage without n, any equity-curve or currency rendering.
- Backfilling or mutating any existing journal record (append-only `verdict_events` untouched; no record edits at all).
- The "re-watch this window" affordance (lands with its own journey later).

## DEFINITION OF DONE

- [ ] Target journey J-59 passes via browser-qa-agent (per the goal.md steps: a handful of resolved theses across setups including at least one abandoned; open the analytics view; every acceptance clause pixel-verified, including the pre-/post-iter-15 fingerprint partition split rendering as separate blocks)
- [ ] Required-still-passing journeys remain green: J-01, J-08, J-50, J-51, J-52, J-54, J-55, J-56, J-57, J-58, J-68 (observer-equivalence suite re-run green; diff contains no engine/classifier/provider/chart file)
- [ ] Carry-along verified: a still-ACTIVE post-v7 thesis shows "not yet resolved" copy (never "predates"), and a pre-feature resolved thesis still shows the "predates the feature" copy, on all three sections
- [ ] No anti-goal violation introduced (specifically: no pooling, no naked percentages, no currency/equity/edge presentation, no prediction language)
- [ ] Unit tests pass; no regressions (full backend suite green)
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-16-dev.md`

## TESTING REQUIREMENTS

- **Browser:** J-59 (full acceptance), plus re-verification passes over J-01, J-08, J-50, J-51, J-52, J-54–J-58, J-68. The J-59 run MUST assert in pixels: (1) two distinct `config_fingerprint` partitions render separately (the iter-15 split — never pooled); (2) the abandonment bucket is visible with its count; (3) an insufficient-sample group shows the marker WITH its n; (4) median spread/R sits beside a +1R figure; (5) the acted-trade block is visually separate from the confirmation-anchored block; (6) no currency symbol / equity curve anywhere on the view. The carry-along needs one capture per fallback state (unresolved "not yet" vs pre-feature "predates").
- **Unit/integration:**
  - analytics module: never-pool pinning (records differing only in `data_feed` or only in `config_fingerprint` land in distinct partitions); abandonment always present in n and as its own bucket; insufficient-sample gating (below min → marker + n, at/above min → full stats); truncated horizons counted separately, never in ternary buckets; acted-trade population structurally disjoint from confirmation-anchored; median time-to-confirm from the persisted timeline (and honest omission with zero confirmations); median spread/R from persisted `spread_at_anchor`/`r_basis`; deterministic output over a fixed temp-DB fixture (two identical calls byte-equal);
  - realized-R reuse: the acted-trade distribution consumes the `marks.py` row-27 function — assert no second formula (e.g. by call-through or shared-helper test);
  - fingerprint stability: changing `analytics_min_sample_size` does NOT change `config_fingerprint` (documented serving-only exclusion);
  - endpoint: `GET /research/analytics` serves the module's projection verbatim; empty journal → honest empty payload (not an error, not fabricated groups);
  - observer-equivalence suite re-run (J-68 invariant).
- **Error cases:** empty journal and empty partitions render honest empty states (taxonomy copy), never fabricated rows; taxonomy-unavailable fallback never hardcodes research labels; the view never computes a percentage client-side.

## NOTES

- **Lessons applied (state/lessons.md):**
  - *iter-15:* an absent key with two causes must get two copies — this is the carry-along, and it applies forward to the analytics empty/insufficient-sample states: distinguish "no records in this group yet" from "below minimum sample" explicitly.
  - *iter-6:* browser QA MUST run against a backend started AFTER dev completes, with a canary probe — `GET /research/analytics` returning the new payload shape is this iteration's natural canary.
  - *iter-3/4/14:* the analytics view will sit below the fold and involves view-switching — full-page captures, scroll the asserted element into view, and sanity-check capture bytes (the 6,303-byte uniform blank-frame defect persists in the tooling; cite only non-blank captures).
  - *iter-0:* any absence claim (e.g. "no pooled rollup", "no currency anywhere") must be evidenced with the server demonstrably up.
- **Seeding the J-59 browser run:** the persistent dev journal DB already holds ~50 theses spanning resolutions (12 played_out / 26 abandoned / 7 expired per iter-15 QA) across two fingerprints — prefer it for the partition-split assertion, and add fresh sim theses only as needed for a group that clears the min-sample threshold.
- **Deliberate decision flagged for the reviewer/evaluator:** `analytics_min_sample_size` is excluded from `config_fingerprint` as serving-only, by the iter-12 page-size precedent and rationale (fingerprinting a display threshold would fragment pools dishonestly). The exclusion must carry the documented rationale comment and the fingerprint-stability unit test named above. All other new values introduced here are aggregation outputs, not thresholds entering computation.
- **Scope flag:** none — everything here is capability 31 verbatim. The hint log portion of the `/journal` page (blueprint IA) is NOT built here; it lands with J-65 in the cue layer.
- Evaluator's iter-15 recommendation followed exactly; depth lean (single read-only endpoint + one view; the FULL pipeline's `qa_complete` harness defect remains open upstream).
