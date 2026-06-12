# goal-i_will_be_super_rich_with_my_loved_ones-iter-18 Execution Plan

Replay-study layer (J-60/J-61/J-62): study runner + seeded null baseline + `/studies` page +
pinned CI reference study. Full depth, multi-surface. The last evidence-layer step before the
cue layer (J-53, J-63–J-67 — strictly OUT of scope).

## What to Build

- **Study runner module** (new `apps/backend/app/research/studies.py`, single owner): unpaced
  offline replay of a chosen source + window through a FRESH `TapeEngine`, attached ONLY via the
  existing observer seam (the `test_real_data_classify.py` / `test_dense_replay_gate.py` pattern).
  NO change to `app/engine/**`, providers, classifier, history buffer, observer seam, or snapshot
  shape — J-68 byte-identity stays green.
- **Three sources through existing seams:** (a) the committed PG SIP fixture
  (`apps/backend/tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json`) loadable without
  credentials; (b) seeded sim scenarios (SIM-REVERSAL, SIM-BUYER/SIM-SHIFT) unpaced; (c) arbitrary
  symbol + past window via the EXISTING historical fetch path (credentialed; existing explicit
  error states on failure — never fabricated data).
- **State-native auto-arming** for `absorption_reversal` / `trend_continuation` from EXISTING
  engine states/features only; every threshold config-owned and IN `config_fingerprint`. Armed
  occurrences run the EXISTING per-setup verdict rule tables (`verdict.py` semantics — no new
  rules/indicators) and record per-occurrence verdict summaries.
- **Level setups** (`level_break`, `failed_move_fade`) require a user-supplied level: stamped
  `hindsight_level`, labeled "level chosen with hindsight — illustrative", excluded from any
  cross-study aggregate (enforced in code + test). No level → 422, never a guess.
- **Deterministic occurrence R definition** (named design decision — document in handoff):
  config-owned rule at arm time (e.g. config spread-multiple on the adverse side of arm price),
  identical for setup and null arms, routed through the EXISTING `marks.py::r_basis` +
  `excursions.py` ternary/horizon machinery (`excursion_horizons_seconds`) — a registered consumer
  of the same formula, never a second one. Never fitted.
- **Excursions per occurrence:** arm-anchored, per config horizon, first-touch in logical time;
  window-end-truncated horizons flagged `truncated` and counted separately — never dropped or
  extrapolated.
- **Seeded random-arm-time null baseline:** `study_null_arm_count` (new config key, IN
  fingerprint) arms from a recorded seed, same window/direction/R definition/horizons; seed
  persisted on the study record. ONE replay pass serves both setup and null arms (in-memory
  observation — never N re-replays; no tape data persisted).
- **Cancellable background jobs:** status enum `queued | running | done | cancelled | failed`
  with progress; cancel honored between events/chunks; cancelled → explicit cancelled with
  partial-marked results; failed → explicit error, never empty success. Replay runs off the event
  loop (worker thread/executor, cooperative yields); ALL SQLite writes through the existing single
  writer queue — never from event processing or WS serialization.
- **API (blueprint row 23, exactly):** `POST /research/studies` (create+start, full 422
  validation), `GET /research/studies`, `GET /research/studies/{id}`,
  `POST /research/studies/{id}/cancel` (404 unknown, 409 terminal). Persist once at defining
  moments (stamps at creation; occurrences + aggregates + baseline at completion/cancellation);
  served VERBATIM — never recomputed at read; the UI computes nothing.
- **Honesty stamps + never-pool:** bound source, `data_feed`, `config_fingerprint`, baseline seed
  stamped at creation; no aggregation across feed or fingerprint; n + caveats always rendered;
  under-minimum groups reuse the insufficient-sample honest marker.
- **Committed reference study (J-62 flip):** CI test pins exact occurrence rows + aggregates +
  null-baseline counts (byte-stable) over the PG SIP fixture AND at least one seeded sim, unpaced,
  no credentials, within `dense_replay_time_budget_seconds`-style config budget; double-run
  determinism for identical (source, fingerprint, seed). Pin key numbers in the dev handoff.
- **Schema:** `studies` + `study_occurrences` already exist (v1 payload-blob shape) — first writes
  land here. PREFER no `store.py` schema change (stays v7). If unavoidable: versioned v8 migration
  + committed v7 old-schema fixture + NO backfill, declared in the handoff.
- **Taxonomy copy (row 24, additive):** study status labels (each status its OWN explicit copy —
  iter-15 lesson), `hindsight_level` label, truncated label (reuse), null-baseline caption,
  journaled-measurements framing, per-status honest-absence copy — all via `GET /research/taxonomy`;
  frontend hardcodes none.
- **Frontend:** flip the pre-registered disabled Studies entry in
  `apps/frontend/components/NavBar.tsx` (line ~28, `enabled: false` → enabled) — the ONLY
  cockpit-adjacent pixel change permitted. New `/studies` page: create form (reference-window
  quick-pick labeled as the committed SIP fixture; sim scenarios; symbol + past window reusing the
  existing symbol search + dd-MM-yyyy shared formatter; setup × direction; level input only for
  level setups with the hindsight warning), job list with status/progress + Cancel, results view
  rendering stored results verbatim (occurrence rows, aggregates side-by-side with the seeded null
  baseline in the goal.md register, ternary outcomes, truncated counted separately,
  `hindsight_level` label, feed + fingerprint stamps, n + caveats, "Descriptive only — not trading
  advice").

## Agents Required
- backend-data: yes -- study runner module, four `/research/studies` endpoints, auto-arming +
  occurrence R + null baseline, background-job lifecycle, first writes to the studies tables,
  config keys + fingerprint discipline, taxonomy copy, the pinned reference-study CI test, and the
  full unit/integration test matrix.
- frontend-ux: yes -- NavBar Studies enablement + the new `/studies` page (create form, job list
  with cancel, verbatim results view with null baseline side-by-side), all copy from row-24
  taxonomy, dark instrument-panel style with loading/empty/error states.

## Frontend Present
Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/research/studies.py` -- NEW single-owner study runner + job manager (fresh
  TapeEngine, observer-only, one replay pass for setup + null arms, cancellation, persist-once)
- `apps/backend/app/research/routes.py` -- wire the four study endpoints + validation (422/404/409)
- `apps/backend/app/research/taxonomy.py` -- additive row-24 studies display copy
- `apps/backend/app/config.py` -- `study_null_arm_count`, arming thresholds/dwell, occurrence-R
  spread multiple (all documented research defaults, IN fingerprint); any serving-only key follows
  the iter-12/16 exclusion pattern (rationale + stability test + counter-test)
- `apps/backend/app/research/store.py` -- repository methods for first writes/reads of `studies` +
  `study_occurrences` through the existing writer queue (NO schema bump preferred; v8 path only if
  unavoidable, with migration + committed v7 fixture)
- `apps/backend/tests/test_studies_*.py` (new files as needed) -- pinned reference study,
  determinism/seed reproducibility, arming counts on seeded sims, hindsight exclusion, never-pool/
  stamps, cancellation, failure paths, fingerprint move/stability pair, full error-case matrix
- `apps/frontend/components/NavBar.tsx` -- enable the `/studies` entry
- `apps/frontend/app/studies/page.tsx` -- NEW route
- `apps/frontend/components/Study*.tsx` (e.g. StudyCreateForm, StudyList, StudyResultsView) -- NEW
- `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-18-dev.md` -- handoff incl.
  pinned reference-study numbers + the documented occurrence-R design decision

## UI Evolution (required if Frontend Present: yes)
- New user-facing capability: create, monitor, cancel, re-run, and read deterministic replay
  studies of the setup grammar over chosen windows, against a reproducible random-arm-time null
  baseline.
- New information displayed: study list with status/progress; per-study results — occurrence rows
  (arm time, verdict summary, per-horizon ternary excursions, truncation flags), aggregates with
  n + caveats, seeded null baseline side-by-side, recorded seed, `hindsight_level` labels, feed +
  config-fingerprint stamps.
- New user actions: create study (source/setup/direction/level), cancel, open results, re-run an
  identical study.
- UI surface changes: new `/studies` page (create form + job list + results view).
- Navigation changes: the persistent nav's Studies entry flips from disabled to enabled — the ONLY
  change visible from existing pages (J-68 sentinel allowance).

## Visual Requirements (required if Frontend Present: yes)
- Component patterns: hand-built panels per the design system (Panel-style surfaces like the
  journal page); a form panel for create, a row list for jobs, a table-like results view modeled
  on `JournalTable`/`AnalyticsView` conventions.
- Layout: NavBar (layout-mounted) + single-column page; results detail below or routed from the
  job list; consistent with `/journal`.
- Key visual effects: dark slate-950 cockpit palette, slate-900/60 panels with slate-800 borders,
  font-mono for ALL numerics; status colors within the existing semantics (amber for
  running/partial/truncated caveats, rose for failed, slate for queued/cancelled) — never green
  "success" framing that reads as edge.
- States to handle: loading; explicit empty ("no studies yet" copy from taxonomy); per-status
  honest-absence copy (each status distinct); explicit error for failed studies and unavailable
  credentialed windows; partial-marked cancelled results; below-the-fold capture discipline
  (full-page, scrolled-into-view — iter-2/3/14 lesson).

## Key Test Scenarios
- J-60 (browser + unit): create a reference-window quick-pick study → status queued→running→done →
  results show occurrence rows + aggregates side-by-side with the seeded null baseline, feed +
  fingerprint stamped; identical re-run reproduces identical numbers in pixels AND REST (verbatim
  equality).
- J-61 (browser + unit): manual-level study shows the `hindsight_level` label (+ code-level
  exclusion test); truncated occurrences flagged and counted separately; mid-run cancel → explicit
  cancelled with partial-marked results (writer queue intact); failing study (no data/provider
  error) → explicit error, never empty success.
- J-62 (CI): committed reference-study test pins exact rows/aggregates/baseline counts over the PG
  SIP fixture + a seeded sim, byte-stable, unpaced, no credentials, within the config budget;
  double-run determinism for (source, fingerprint, seed); iter-17 engine-gate tests untouched and
  green.
- Error matrix: unknown setup/direction/source → 422; level setup without level → 422;
  future/empty/invalid window → 422 or explicit failed; cancel unknown id → 404; cancel terminal →
  409; arbitrary window without credentials → explicit unavailable, never fixture-substituted.
- Regression: `test_observer_equivalence.py` 7/7; `test_dense_replay_gate.py` green;
  full backend suite green (629+ tests, zero re-pins — verify by EXIT CODE, the `addopts = "-q"`
  double-quiet suppresses the count line); frontend builds clean; J-68 sentinel re-verified in
  pixels (cockpit unchanged except the enabled Studies entry); fingerprint tests — new study keys
  MOVE the fingerprint; any serving-only key has the stability + counter pair.
- Browser QA discipline: backend started AFTER dev with a canary probe (`GET /research/taxonomy`
  must contain the new studies copy); persistent dev DB (`apps/backend/tapeology_journal.db`) for
  multi-fingerprint stamp pixels; `/studies` reachable in ≤2 clicks.

## Assumptions & Notes
- Blueprint protocol is ALREADY satisfied: `state/blueprint.md` carries the iter-18 nav-skeleton +
  row 23/24 build-out notes and `state/blueprint.reapproval-requested` exists (verified). No
  further blueprint edit needed unless the implementation deviates.
- Schema stays v7 — the v1 payload-blob shape of `studies`/`study_occurrences` should absorb the
  study record (stamps/seed/status in the payload). Take v8 ONLY if a column is genuinely
  unavoidable, with the full iter-4 migration discipline.
- Performance: one unpaced PG-fixture replay ≈10 s (iter-17), dominated by
  `_window._refresh_rebuilds`; budget job runtime + the CI pin accordingly. Do NOT touch engine
  perf — engine files are out of scope.
- Diff confinement (reviewer verifies): app code only under `app/research/**`, `app/config.py`,
  routes wiring, and `apps/frontend/**`; NO engine/provider/classifier/store-schema file unless
  the declared v8 path was taken.
- `qa_complete` harness-defect fallback: completion must not depend on audit/closure artifacts;
  the goal-evaluator independently re-runs the pinned tests + suites and opens the `/studies` and
  J-68 pixels. If the harness hard-blocks before QA, complete lean-style
  (developer → reviewer → browser-qa) with the same evaluator re-runs.
- Copy register: every studies string descriptive, present-tense, measurement-framed — n and
  caveats always visible; this is the most edge-claim-prone surface in the product.
- Out of scope (do not build): the cue layer (J-53, J-63–J-67), `delivery_lag_seconds`, hint
  baseline citation, any cross-study aggregate VIEW, parameter sweeps/multi-config studies,
  watchlists/scanning, any change to `/research/analytics`.
