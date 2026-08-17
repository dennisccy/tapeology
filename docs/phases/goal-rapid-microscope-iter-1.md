# Goal Iteration 1 — Microscope Readiness: an honest corpus inventory lands on /desk

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 1
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01
- **Required-still-passing journeys:** J-10 (its canonical home — `/`, `/structure`, `/desk`'s
  every shipped section — includes the exact `/desk` page this iteration edits; its sentinel
  half must stay at least as verified as iteration 0 left it)
- **Anti-goal reminders (selected; full text governs — see `docs/goal.md` §Anti-goals):**
  - *Immutable rail 3 — Frozen foundations:* "the `v1` strategy, the `default` profile, the tape
    engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`,
    and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned
    beside them, never a mutation of them. *(critical)*"
  - *Immutable rail 6 — Single source of truth:* "each shared value is computed once, owned by
    one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor
    hard-fails violations. *(critical)*"
  - *Immutable rail 9 — Immutable data:* "registered datasets and bar series are append-only,
    checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at
    registration. *(critical)*"
  - *Rapid-Microscope anti-goal:* "No microstructure claim beyond what L1 supports.
    `refill_consistent` is the strongest liquidity label; 'iceberg', institutional-intent, and
    manipulation language are banned; every aggressor-derived quantity is served beside its
    `fallback_frac` and `unknown_frac`. *(critical)*"
  - *Rapid-Microscope anti-goal:* "The 12 pre-existing tick symbol-days are permanently
    exploratory — never sealed, never `historical_oos`, never relabeled. *(critical)*"
  - *Rapid-Microscope anti-goal:* "The ~150-symbol-day research-readiness gate is never lowered
    or silently satisfied; any claim whose predeclared floor is unmet fails closed with the
    floor arithmetic served. *(critical)*"

## GOAL

Ship the era's first honest, browser-visible statement of what tick evidence actually exists: a
new read-only `micro_readiness.py` endpoint plus a "Microscope Readiness" panel on `/desk` that
together report the real 12-symbol-day legacy corpus, its per-shard quality, and which of the
three predeclared pilot-study floors it clears today (none, honestly).

## BACKGROUND

Iteration 0 was a verify-only baseline: it confirmed J-01's transition documents and recorded
the era-open reference numbers (suite 2,691 pass / 8 skip, fingerprint `08e471b10130e1e2`, the
six `referee_*.py` SHA-256 hashes), but J-01's own remaining steps — the readiness module, its
endpoint, and the `/desk` panel — were never built, and the iter-0 evaluator explicitly
recommended building exactly this, alone, next: "Everything else in this era depends on that
corpus-truth surface existing." Per the priority rubric this is simultaneously the unblocker
(rule 3) and the smallest remaining spec (rule 4) — nothing regressed (rule 1 moot) and the last
`coherence.md` does not exist yet, so rule 2's consolidation trigger does not apply either.
Depth stays `lean`, matching the evaluator's binding recommendation for this iteration: no full
trigger holds — this is a single new backend module plus one new endpoint plus its one UI use,
the textbook lean example named in the agent instructions itself ("a new endpoint plus its UI
use"); it is not a structural/cross-cutting refactor (trigger 1), it introduces a brand-new
Data-Contract value rather than changing an already-registered one (trigger 2 explicitly
excludes purely additive work), the prior verdict was `CONTINUE` not `ESCALATE` (trigger 3), and
the hardening-cadence counter is 0 of 6 (trigger 4). The goal's own "Iteration hygiene" note
(step timeouts tripped in 13 of 15 iterations last era) further argues for staying narrow.
Applying `lessons.md` iter-0: the backend suite must be invoked as `pytest tests/` with no added
`-q` (the project's `pyproject.toml` already sets it, and stacking hides the final summary
line), and `status.json`'s `browser_checks_run` flag is stale — trust
`reports/phase-*-ui-test-results.md` and the evidence directory instead. Two interpretation
calls this iteration required (session-equivalents formula; per-study floor reading, since
`docs/rapid-validation-spec.md` has no dedicated readiness section) are logged to
`runs/goal-session-rapid-microscope/state/assumptions.md`. The iteration-0 evaluator also flagged
that the coherence audit has never run and should once the era's first new served value lands —
that is this iteration; see NOTES.

## IN SCOPE

### Backend

- [ ] New module `apps/backend/app/research/micro_readiness.py` aggregating the 18 legacy tick
      datasets into a served-from-disk corpus inventory. Reads existing `DatasetStore.list()`
      metadata (`symbol`, `window_start_utc`/`window_end_utc`, `data_feed`,
      `event_counts.trades`/`.quotes`, `checksum`, `split`) verbatim — never a second parse or
      re-derivation of a value `datasets.py` already owns.
  - Per-shard rows: derive `session_date` via the existing session-honesty module
    (`desk_sessions.py` — spec §0 names it "the arbiter of what counts as a session"; reuse its
    ET-date conversion rather than inventing a second one), `bytes` via file size, and
    `coverage_gaps` from the window bounds vs. full RTH (09:30–16:00 ET) — all cheap, no event
    replay needed.
  - Per-shard `fallback_frac`: the ONE genuinely expensive per-shard computation (replays each
    dataset's trade/quote stream through `aggressor.classify_aggressor`). Cache it keyed on the
    dataset's existing content `checksum` (mirrors `dataset_index.py`'s derived/rebuildable
    precedent — losing the cache loses nothing, the next GET rebuilds it) so a repeat request
    does not re-replay ~0.92 GB of tick events (T-8 / Key Capability 9: "page-load GETs never
    compute").
  - Every legacy shard tagged `split_provenance: "hand_assigned"` and
    `exposure_state: "exploratory"` (spec §7.7 — permanent, never sealed, never relabeled).
  - Corpus totals: `distinct_symbol_days`, `distinct_datasets`, `rth_minutes_covered`,
    `session_equivalents`, and `referee_tick_gate_symbol_days` — the last read verbatim via
    `import` from `referee_evidence.REFEREE_TICK_GATE_SYMBOL_DAYS` (150), never a second
    hardcoded constant (single-source-of-truth rail).
  - Per-study floor table for the three J-09-predeclared pilot studies (see Data-contract
    additions for the exact reading) compared against the existing frozen
    `WF_TRAIN_MIN_SESSIONS` + `WF_TEST_MIN_SESSIONS` geometry floor (spec §1) — no invented
    constant.
  - Surfaces `DatasetStore.list()`'s own `errors` rows (corrupt-file integrity failures)
    verbatim in the response — never silently dropped, never a crash.
- [ ] New route `GET /research/desk/micro/readiness` in a new
      `apps/backend/app/research/micro_routes.py` (a fresh router/file mounted separately in
      `main.py`, mirroring `referee_routes.py`'s own precedent and rationale — this file grows
      with J-02 through J-09's routes across later iterations), depending on the EXISTING
      `routes.get_dataset_store` provider — never a second, redefined one.
- [ ] Extend `apps/backend/tests/test_desk_ui_guards.py` `_PRICE_ARITHMETIC_FIELDS` with the
      Microscope Readiness panel's own served numerics, plus a seeded counter-test proving the
      guard can fail (Constraints: "gains every served micro numeric").

### Frontend

- [ ] Add a "Microscope Readiness" section to `apps/frontend/app/desk/page.tsx`, appended
      directly BELOW the shipped "Referee Runs" section (the current last section, `mt-6`
      spacing) — new `data-testid`s only, no shipped `data-testid` or heading string reused
      (T-11). Reuses the shipped `CollapsibleSection` component and the collapsed-by-default /
      deferred-GET-until-expanded pattern already used by Referee Registry/Adjudications/Runs —
      no new UI primitive.
  - Totals line: distinct symbol-days, RTH minutes, session-equivalents, shown beside the
    referee tick-gate figure — every number read verbatim from the GET response body, zero
    client-side arithmetic.
  - Per-shard table (18 rows): symbol, session date, feed, window, trade/quote counts, bytes,
    coverage gaps, `fallback_frac`, checksum, split provenance, exposure state.
  - Floors table (3 rows): one per predeclared pilot study, floor met/unmet.
  - Honest empty/degraded copy for the `integrity_errors` case (design-direction house style:
    e.g. a corrupted-file line, never a silent omission).

### New user-facing capability

For the first time this era, the user can see — from the `/desk` page, not just by reading
files — an honest inventory of exactly what tick data exists on disk today and whether it
clears the bar for any real research question.

### New information displayed

Corpus totals (12 symbol-days, ~3.0 session-equivalents, RTH minutes) shown beside the
referee's existing 150-symbol-day gate; the 18-shard inventory table (symbol / date / feed /
window / counts / bytes / coverage / `fallback_frac` / checksum / split provenance / exposure
state); the three-pilot-study floor table (today: all `floor_unmet`).

### New user actions

Expand the collapsed "Microscope Readiness" section on `/desk` to load it — no compute button,
no operator act; this is a plain read, matching Key Capability 1.

### UI surface changes

`/desk` gains exactly one new section, below the three shipped Referee sections. No other
section, page, or route changes.

### Product surface delta

`/desk` moves from {Playbook · Band Context · Cohorts · Referee (Registry/Adjudications/Runs)}
to those same sections PLUS the era's first honest self-assessment of the evidence base
everything else in Rapid Microscope will build on. Cockpit and `/structure` are untouched.

### Blueprint conformance

`/desk` → Rapid Microscope → Microscope Readiness — the home already registered in
`runs/goal-session-rapid-microscope/state/blueprint.md`'s Information Architecture at baseline.
No nav-skeleton change; no blueprint edit needed this iteration (the module+endpoint pairing was
already pre-registered in the Data Contract table verbatim from `docs/goal.md` §Product Shape,
and this iteration is additive at that same granularity, not a change to it).

### Data-contract additions

`GET /research/desk/micro/readiness`, owned solely by `app/research/micro_readiness.py`
(pre-registered in `blueprint.md`; module/endpoint pairing unchanged — see Blueprint
conformance). Response shape, every field newly served this iteration:

```
{
  "totals": {
    "distinct_symbol_days": int >= 0,                 // 12 today
    "distinct_datasets": int >= 0,                     // 18 today
    "rth_minutes_covered": float >= 0,                 // sum of per-shard RTH-overlap minutes
    "session_equivalents": float >= 0,                 // rth_minutes_covered / 390; ~3.0 today
    "referee_tick_gate_symbol_days": int                // read verbatim from
                                                         // referee_evidence.REFEREE_TICK_GATE_SYMBOL_DAYS (150)
  },
  "shards": [
    {
      "dataset_id": str, "symbol": str, "session_date": str (ISO date),
      "data_feed": str, "window_start_utc": str, "window_end_utc": str,
      "trade_count": int >= 0, "quote_count": int >= 0, "bytes": int >= 0,
      "coverage_gaps": [str, ...],                      // empty when fully covered
      "fallback_frac": float in [0.0, 1.0],
      "checksum": str, "split_provenance": "hand_assigned",
      "exposure_state": "exploratory"
    }, ...                                               // 18 entries today
  ],
  "study_floors": [
    {
      "study_id": "range_wall_failed_aggression" | "delta_divergence_level_tests"
                  | "capitulation_exhaustion",
      "floor_name": "wf_fold_geometry",
      "required_sessions": 60,                          // WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS
      "available_sessions": int >= 0,                    // 11 today
      "status": "floor_met" | "floor_unmet"
    }, ...                                               // 3 entries
  ],
  "integrity_errors": [ {"file": str, "error": str}, ... ]  // DatasetStore.list()'s own error rows, verbatim
}
```

No value here is computed a second time anywhere else: `checksum`/`trade_count`/`quote_count`/
`split` are read verbatim from `DatasetStore.list()`; `referee_tick_gate_symbol_days` is read
verbatim from `referee_evidence.py`; nothing new is added to blueprint.md since the
module+endpoint row already exists there.

## OUT OF SCOPE

- Any change to another `/desk` section (Playbook Evidence, Band Context, Cohorts, Referee
  Registry / Adjudications / Runs) — read `referee_evidence.py` for one constant, touch nothing
  in it or any other `referee_*` module.
- Scout Ledger / Walk-Forward / Validation Vault sections (J-04 / J-05 / J-06 — later
  iterations); `micro_join.py` (J-03); the observer seam, `micro_observer.py`,
  `micro_snapshots.py`, `micro_features.py` (J-02).
- Any new MCP tool — the surface stays at 22 tools this iteration; `desk_micro_readiness` lands
  in J-08.
- A compute manager or `POST` endpoint for readiness — this is a plain `GET`, matching the
  Data Contract table (unlike snapshots/scout/walkforward/vault/recorder, readiness has no
  compute-manager subpath).
- Any TR-1…TR-22 trap implementation — J-01 claims none of them; they land in J-02 through J-10.
- Any new `Config` field or engine change — the fingerprint stays `08e471b10130e1e2`.
- Registering the three pilot studies' actual Scout specs — that is J-09's work, 8 iterations
  away; this iteration only names them in a floor-comparison table.

## DEFINITION OF DONE

- [ ] J-01 passes via browser-qa-agent: `GET /research/desk/micro/readiness` serves the shape
      above with the real corpus values, and the `/desk` Microscope Readiness section renders
      those same served values verbatim (element screenshot).
- [ ] J-10's sentinel half (cockpit `/`, `/structure` load, every shipped `/desk` section)
      remains at least as verified as iteration 0 left it — zero regression introduced by the
      new section landing on the same page.
- [ ] No anti-goal violation introduced (immutable rails 3/6/9 and the three Rapid-Microscope
      rails above re-checked; full anti-goal table re-verified by the evaluator).
- [ ] Unit tests pass; no regressions — backend suite count stays ≥ 2,691 pass / 8 skip, the
      fingerprint stays `08e471b10130e1e2`, and all 6 `referee_*.py` SHA-256 hashes match
      iteration 0's recorded listing exactly.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-1-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-01 (Microscope Readiness section — expand if collapsed, element-capture per T-10)
  and J-10's sentinel (cockpit `/`, `/structure` load + Tradable Map, every shipped `/desk`
  section: Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs), all via the
  store-scoped rig (`:8301`/`:3301`), clean rebuild first (`rm -rf apps/frontend/.next`, T-9).
- Unit/integration: `micro_readiness.py` against the REAL legacy corpus (the acceptance values
  ARE the real 18-dataset/12-symbol-day counts — a fixture cannot substitute for this check),
  plus a small synthetic fixture (hermetic, no network) for the corrupted-file and cache-hit
  edge cases; the extended `_PRICE_ARITHMETIC_FIELDS` guard and its seeded counter-test; the
  full backend suite re-run as `pytest tests/` with no added `-q` (lessons.md iter-0) alongside
  the fingerprint check and the 6-file referee SHA-256 re-check against iteration 0's listing.
- Error cases: a hand-corrupted legacy dataset file's `DatasetIntegrityError` is surfaced in
  `integrity_errors` — never a crash, never a silently-dropped shard, and the other 18 real
  shards are still present in `shards` with their fields populated alongside it.

Test-first contract:

- TC-1: given the 18 registered legacy tick datasets on disk, when `GET
  /research/desk/micro/readiness` is called, then `totals.distinct_symbol_days == 12` and
  `totals.distinct_datasets == 18`.
- TC-2: given the same corpus, when `totals` is computed, then `totals.session_equivalents`
  reads within [2.9, 3.1] (goal.md's stated ≈3.0; Build anchors record ~3.01) and
  `totals.referee_tick_gate_symbol_days == 150`, asserted via direct equality against the
  imported `referee_evidence.REFEREE_TICK_GATE_SYMBOL_DAYS` constant, never a duplicated
  literal.
- TC-3: given each of the 18 shard rows, when read from the response, then every row carries
  `split_provenance == "hand_assigned"`, `exposure_state == "exploratory"`, and `fallback_frac`
  in `[0.0, 1.0]`, with the corpus-wide spread of values falling inside the 0.29–0.76 band Build
  anchors records.
- TC-4: given each shard row, when compared against `DatasetStore.list()`'s own metadata for the
  same `dataset_id`, then `checksum`, `trade_count`, `quote_count`, and `split_provenance`'s
  underlying split value are byte-identical to the store's existing values.
- TC-5: given the three predeclared pilot studies and today's 11-session legacy corpus, when
  `study_floors` is served, then all three rows read `status == "floor_unmet"` with
  `required_sessions == 60` and `available_sessions == 11`.
- TC-6: given a synthetic fixture with one dataset file whose stored checksum has been
  hand-corrupted, when readiness aggregates the corpus, then that file's error is surfaced as an
  entry in `integrity_errors` (never dropped, never a 500), and the fixture's other healthy
  shards still appear in `shards` with every field populated, unaffected by the corrupted one.
- TC-7: given the endpoint has already been called once for an unchanged corpus, when it is
  called a second time, then the per-shard `fallback_frac` classification path is not re-run
  from raw events (asserted via a call-count spy in the unit test) and the second response body
  is byte-identical to the first.
- TC-8: given the `/desk` page freshly rebuilt and loaded via the store-scoped rig, when the
  Microscope Readiness section is expanded, then the totals line, the 18-row shard table, and
  the 3-row floors table show the same values `GET /research/desk/micro/readiness` served,
  captured as an element screenshot.
- TC-9: given `apps/frontend/app/desk/page.tsx`'s new Microscope Readiness section source, when
  `test_desk_ui_guards.py`'s extended `_PRICE_ARITHMETIC_FIELDS` pattern scans it, then no
  expression combines a served readiness numeric with `+`/`-`/`*`/`/`; a seeded violation (e.g.
  dividing `distinct_symbol_days` by `referee_tick_gate_symbol_days`) is caught by the
  counter-test.
- TC-10: given the full backend suite and the era-open baseline (2,691 pass / 8 skip, fingerprint
  `08e471b10130e1e2`, the 6 referee-module SHA-256 listing from iteration 0), when re-run this
  iteration, then the suite count is ≥ 2,691 pass with 0 new failures, the fingerprint is
  unchanged, and all 6 referee SHA-256 hashes match iteration 0's listing exactly.
- TC-11: given the shipped `/desk` sections and the cockpit/`/structure` pages, when
  browser-qa-agent re-verifies them this iteration, then every one renders exactly as iteration
  0's screenshots showed, with zero `data-testid` or copy change anywhere outside the new
  Microscope Readiness section.
- TC-12: given the iteration completes, when the developer writes the handoff, then
  `docs/handoffs/goal-rapid-microscope-iter-1-dev.md` exists and records the readiness response
  shape, the corpus totals, and the suite/fingerprint/referee-hash re-check results.

## NOTES

- Two interpretation calls were logged to `runs/goal-session-rapid-microscope/state/assumptions.md`
  as `iter-1 — goal-decomposer`: (1) `session_equivalents = rth_minutes_covered / 390` (standard
  RTH minutes), chosen because it reproduces goal.md's own stated ~3.0 on today's corpus and no
  spec section defines a different formula; (2) all three pilot studies read the SAME existing
  `WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS` geometry floor, since no study-specific floor is
  spec'd yet (J-09 is 8 iterations away) and either reading yields the acceptance-mandated
  `floor_unmet` outcome for all three today. Both are marked reversible — descriptive columns
  only, no gate depends on either reading.
- The iter-0 evaluator flagged that no coherence audit has ever run for this session and that it
  should run "once the first new served value lands" — this iteration is that trigger. Depth
  stays `lean` per the binding recommendation regardless; whether/when the coherence-auditor
  runs is an engine-level scheduling decision outside this spec's control, not a lean/full
  choice.
- Per `lessons.md` iter-0: run the backend suite as `pytest tests/` (no extra `-q`); do not trust
  `status.json`'s `browser_checks_run` flag — use `reports/phase-*-ui-test-results.md` and the
  evidence directory instead.
- `apps/frontend/app/desk/page.tsx` is ~10,800 lines; this iteration's frontend change is
  strictly additive (one new section appended after "Referee Runs", the current last section) —
  no existing line in the file is edited, matching the exact pattern the three shipped Referee
  sections themselves used one iteration each.
