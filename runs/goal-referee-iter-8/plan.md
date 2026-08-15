# goal-referee-iter-8 Execution Plan

Era 6 "The Referee" · Journey J-07 ("The starter family — historical exploration becomes
registered questions") plus two write-side riders, both already root-caused by the prior
iteration's evaluator. Depth is **full** (mandatory — prior verdict was ESCALATE).

## What to Build

- **Starter-family shortlist fold** in `referee_registry.py`: five spec-§7-pinned module
  constants (S-1..S-5 — `capitulation:long`/A/`5m`, `jbe:long`/A/`1h`, `double_top:short`/A/
  `to_close`, `range_trade:long` `at_wall`/B/`1h`, `range_trade:long`+`at_wall`/C/`1h`) plus a
  function computing LIVE readiness (`n`, `n_sessions`, `accrual_rate_sessions_per_day`,
  `projected_days_to_target`) — reusing `referee_evidence.playbook_occurrence_readiness()`'s
  existing per-`(setup_id, side)` pooling for the three estimand-A candidates and the existing
  band-context/backing-bucket resolution for the two `at_wall` candidates. Never a second
  pooling implementation.
- **New `GET /research/desk/referee/registry/shortlist` route** in `referee_routes.py` serving
  that fold (plain read; GET never computes, T-8).
- **`discovery` block** — a field addition on each hypothesis entry already served by
  `GET /research/desk/referee/registry`: pre-boundary (`session_date <= confirmation_start_
  boundary`) observations in the hypothesis's own `(setup_id, side)` cell, reusing
  `_hypothesis_accrual`'s existing pooling primitives and its already-hardened
  `confirmation_start_boundary` field verbatim (never re-derived, never client-supplied — the
  iter-6 lesson this spec explicitly calls out). Never contributes to the existing `accrual`
  block.
- **Rider 1** (write-side attestation gate): `run_evaluation_and_record` must never mint
  `role: "checkpoint"` — and therefore never write the one permanent adjudication snapshot —
  when `attestation["passed"]` is `False`.
- **Rider 2** (integrity disclosure parity): `adjudications_response()` must surface
  `hypothesis_store.list()`'s integrity errors as a new `integrity_errors` key, the same way
  `GET /registry` already does, instead of silently discarding them.
- **Guard extension**: every new served referee numeric this iteration (shortlist readiness
  fields, `discovery.n`/`discovery.n_sessions`) added to `test_desk_ui_guards.py`'s
  `_PRICE_ARITHMETIC_FIELDS`, with seeded counter-tests proving the guard actually fires.
- **Frontend — first Referee UI slice**: a new **Referee Registry** `CollapsibleSection` on
  `/desk`, rendered below every shipped section — the shortlist table (5 rows, readiness
  numbers, rationale sentences), a select + explicit confirmation step, POST to the existing
  `POST /registry/hypotheses` act; the registered-hypothesis row (boundary, target,
  `origin: historical-exploration`); the `discovery (exploratory)` label rendered distinct from
  `accrual`; the honest `"No hypotheses registered."` empty state; `lib/api.ts`/`lib/types.ts`
  additions (this project's FIRST-EVER frontend bindings for any referee endpoint — nothing
  referee-related exists in `lib/api.ts`/`lib/types.ts`/`page.tsx` today, confirmed by direct
  search).

**Out of scope this iteration** (per the phase spec — do not build): J-08 (strategy family +
promotion interlock), J-09 (Referee Adjudications / Referee Runs sections, withdrawal display,
MCP v5); any change to `desk_forward.py`, `desk_playbook*.py`, `levels.py`, `tradability.py`,
`pnl_scan.py`, `app/config.py` (frozen this whole era); any change to the five shortlist
candidates' own definitions (spec §7 is pinned verbatim); new `Config` fields (zero expected,
fingerprint `08e471b10130e1e2` must not move); fabricating the operator's real 2–3 production
registrations (optional, operator-gated — the honest not-yet-acted state is a valid pass, per
goal.md's own J-07 acceptance text).

## Agents Required

- backend-data: yes — the shortlist fold + route, the `discovery` fold, Rider 1 (attestation-
  gated `role`), Rider 2 (`integrity_errors` on `/adjudications`), the guard-list extension, and
  the backend test suite (TC-1, TC-2, TC-6, TC-7, TC-8, TC-9, TC-10, TC-11).
- frontend-ux: yes — the Referee Registry `CollapsibleSection`, the shortlist table + select/
  confirm/submit flow, the registered-hypothesis + `discovery` rendering, the empty state, and
  the first-ever `lib/api.ts`/`lib/types.ts` referee bindings (TC-3, TC-4, TC-5, TC-12).

## Frontend Present

Frontend Present: yes

This is the first real browser-usable Referee action of the whole era — the operator can, for
the first time, see and act on Referee machinery from `/desk` rather than only through keyless
backend tests.

## Files to Create/Modify

- `apps/backend/app/research/referee_registry.py` -- add the five S-1..S-5 shortlist module
  constants, a `shortlist_response()`-style fold function (live readiness), and a `discovery`
  fold function reusing `_hypothesis_accrual`'s pooling; wire `discovery` into
  `registry_response()`'s per-hypothesis dict.
- `apps/backend/app/research/referee_routes.py` -- new `GET .../registry/shortlist` route
  (mirrors the existing `GET /registry` wiring style at line ~253).
- `apps/backend/app/research/referee_adjudicate.py` -- **Rider 1**: in
  `run_evaluation_and_record` (role decision at line ~1038-1042, attestation computed at line
  ~1070, consumed at line ~1141 `if recorded["role"] == "checkpoint":`) — downgrade
  `fields["role"]` from `"checkpoint"` to `"pending"` when `not fields["attestation"]["passed"]`,
  BEFORE `evaluation_store.record(fields)` at line ~1135, so the false-attestation case never
  reaches the snapshot-write branch. **Rider 2**: in `adjudications_response()` (line ~1407,
  currently `hypotheses, _errors = hypothesis_store.list()` — the errors are discarded), thread
  those errors into the returned dict at line ~1425 as a new `"integrity_errors"` key, mirroring
  `referee_registry.registry_response()`'s existing four-store error-concatenation pattern
  (line ~840-849).
- `apps/backend/tests/test_referee_registry.py` -- shortlist fold tests (5-candidate shape,
  zero-corpus divide-by-zero guard, live vs static numbers), `discovery` fold tests (including
  the deep-backfilled-after-registration boundary counter-test), route-level tests for the new
  GET; NOTE this file already carries a `_starter_family_payloads()` helper (line 516-565, TC-14)
  with the exact S-1..S-5 field values used to test registration — mirror those same values as
  the new PRODUCTION module constants (the two serve different purposes: that helper is
  test-only registration fixtures; the shortlist needs its own production constants in
  `referee_registry.py`), and the S-7 spec table's own "corpus at authoring" numbers are
  authoring-time illustrations only — never hardcode them, this journey's whole point is a LIVE
  read.
- `apps/backend/tests/test_referee_adjudicate.py` -- Rider 1 test (TC-7: forced
  `attestation.passed=False` → stored `role` is `"pending"`, no snapshot written), Rider 2 test
  (TC-8: corrupted hypothesis file → named in `/adjudications`' `integrity_errors`).
- `apps/backend/tests/test_desk_ui_guards.py` -- extend `_PRICE_ARITHMETIC_FIELDS` (currently
  ends around line 247) with the new shortlist/discovery numeric field names actually used in
  the JSX, plus seeded counter-tests proving the guard fires on a deliberately-broken fixture.
- `apps/frontend/app/desk/page.tsx` -- add `"refereeRegistry"` to the `DeskCollapsibleSection`
  union (line ~330-336); add a new `<section aria-label="Referee Registry">` +
  `<CollapsibleSection id="refereeRegistry" ...>` block directly below the existing "Playbook
  Evidence" section (the current last section, line ~9256-9271) — new `data-testid`s only (T-11,
  never reuse a shipped one); wire the deferred-fetch `sectionReadIssuedRef` pattern the same way
  every other section already does (see line ~7453/7467 for the convention).
- `apps/frontend/lib/api.ts` -- new functions for `GET .../registry/shortlist`, the extended
  `GET .../registry` consumption (now carrying `discovery`), and `POST .../registry/hypotheses`
  (this project's first-ever referee API bindings — none exist today).
- `apps/frontend/lib/types.ts` -- `ShortlistCandidate` type, extended hypothesis-entry type with
  the `discovery: {n, n_sessions, label}` block.
- `docs/handoffs/goal-referee-iter-8-dev.md` -- new dev handoff.
- `runs/goal-session-referee/state/assumptions.md` -- append the interpretation calls this
  iteration is likely to need logged (see Notes below), consistent with every prior iteration's
  practice in this session.

## UI Evolution

- **New user-facing capability**: the operator can, for the first time, open `/desk`, see the
  Referee's five pre-registered candidate research questions with live sample-size readiness and
  rationale, and register one directly through an explicit confirm step — producing a permanent,
  boundary-stamped hypothesis.
- **New information displayed**: the five spec-pinned shortlist candidates (estimand, setup/
  side, primary measure/horizon, rationale sentence, live `n`/`n_sessions`/accrual-rate/
  projected-days-to-target); after registration, that hypothesis's boundary date, target session
  count, and `historical-exploration` origin; the `discovery (exploratory)` label on a
  registered hypothesis's pre-boundary historical numbers, visibly distinct from its `accrual`
  numbers.
- **New user actions**: select a shortlist candidate, review its live readiness, complete an
  explicit confirmation step, submit the registration.
- **UI surface changes**: one new Referee Registry `CollapsibleSection` on `/desk`, rendered
  below every shipped section (below the current last section, "Playbook Evidence"). No existing
  section, column, or behavior changes anywhere on the page.
- **Navigation changes**: none — nav stays exactly Cockpit `/` / Structure `/structure` /
  Desk `/desk`; no new route.

## Visual Requirements

- **Component patterns**: reuse the established `Panel` + `CollapsibleSection` wrapper
  (`apps/frontend/components/CollapsibleSection.tsx`) exactly as the six existing `/desk`
  sections already do — the most recent precedent is the "Playbook Evidence" section
  (`page.tsx` ~line 9262-9270). Shortlist rows render as a plain dense table — this house style
  is explicitly "tables and text, no dashboard cards/gauges" (blueprint.md's Layout shell).
  Reuse the page's existing `PRIMARY_BUTTON_CLASS`/`CANCEL_BUTTON_CLASS`-style Tailwind button
  constants for the select/confirm/cancel controls rather than inventing new button styling.
- **Layout**: unchanged persistent top nav + single main-content column; the new section slots
  in as the new LAST `<section aria-label="...">` + `mt-6` block, matching every prior section's
  wrapper convention exactly.
- **Key visual effects**: none beyond the established look (dark-only, dense, terminal-grade —
  no glassmorphism/glow anywhere on this page today). The `discovery (exploratory)` label and
  any verdict-adjacent text must read as plain typographic labels, never a colored badge — the
  Design Direction is explicit that "no color implies advice," and this section is a lab
  notebook, not a scorecard.
- **States to handle**: the honest `"No hypotheses registered."` empty state when zero
  hypotheses exist; the shortlist must always render its 5 rows even against an all-zero-
  readiness corpus (never blank, never a divide-by-zero crash on `projected_days_to_target`); a
  distinct "candidate selected, awaiting confirmation" state between select and submit; the
  existing deferred-fetch loading convention (`sectionReadIssuedRef`) on first expand; an honest
  inline error message if the POST is refused (422 malformed/duplicate, 409 conflict) — never a
  silent failure.

## Key Test Scenarios

Directly from the phase spec's test-first contract (every DEFINITION OF DONE line maps to one
of these):

- TC-1: `GET .../registry/shortlist` returns exactly 5 candidates, ids `S-1`..`S-5`, each with
  non-negative `n`/`n_sessions`/`accrual_rate_sessions_per_day`/`target_sessions`/
  `min_occurrences`.
- TC-2: a zero-corpus `jbe:long` cell serves `S-2` with `n: 0`, `n_sessions: 0`,
  `accrual_rate_sessions_per_day: 0`, `projected_days_to_target: null` — never divide-by-zero.
- TC-3 (browser): the Referee Registry section expands and renders all 5 shortlist rows with
  rationale + readiness numbers on the fixture rig — screenshot.
- TC-4 (browser): selecting S-4 and completing the confirm step POSTs
  `.../registry/hypotheses` with `confirm: true`; the response's `hypothesis_id`,
  `confirmation_start_boundary`, `target_sessions`, `origin: "historical-exploration"` render in
  the registered-hypotheses row — screenshot.
- TC-5 (browser): a hypothesis with pre-boundary historical signals on file shows a
  `discovery (exploratory)` label beside its historical count, distinct from `accrual` —
  screenshot.
- TC-6: against the REAL store, with no operator action taken, the shortlist still serves 5
  candidates and `hypotheses: []` — the honest not-yet-acted state, never fabricated.
- TC-7: a forced `attestation.passed=False` evaluation stores `role: "pending"` (never
  `"checkpoint"`), and writes no adjudication snapshot (Rider 1).
- TC-8: a corrupted hypothesis file alongside a valid checkpointed one is named in
  `GET .../adjudications`'s `integrity_errors`, not silently dropped (Rider 2).
- TC-9: a non-shortlist payload (e.g. `dbi:short`, estimand A) still registers successfully —
  proving the write path stays generic, never restricted to S-1..S-5.
- TC-10: a deep-backfilled pre-boundary record recorded AFTER registration contributes to
  `discovery.n_sessions`, never to `accrual.informative_post_boundary_sessions` — proving
  `session_date`, not `recorded_at`, gates the boundary.
- TC-11: full backend suite collected count >= 2,642, 0 failed;
  `Config().config_fingerprint()` prints `08e471b10130e1e2`.
- TC-12 (browser): after `rm -rf apps/frontend/.next` + rebuild, every shipped `/desk` section
  renders exactly as shipped alongside the new Referee Registry section — screenshots for each
  (J-10 regression sentinel).

## Notes

- **Riders are pre-diagnosed, not exploratory** — both bugs were confirmed by direct code
  reading before this plan was written (see Files to Create/Modify for exact line pointers).
  This should keep both fixes surgical rather than open-ended investigations.
- **Two likely under-specified points worth an `assumptions.md` entry**, matching this session's
  established practice of logging interpretation calls rather than guessing silently:
  1. `accrual_rate_sessions_per_day`'s exact formula is not pinned by
     `docs/referee-statistical-spec.md` §7 (it only lists static authoring-time corpus counts,
     not an accrual-rate methodology) — no existing helper for "sessions per day" was found in
     `referee_evidence.py`/`referee_registry.py`. Pick a reasonable, honestly-disclosed basis
     (e.g. `n_sessions` over the corpus's own recorded session-date span) and log the exact
     formula.
  2. Whether the `discovery` fold applies the same stale-`detector_basis` exclusion
     `_hypothesis_accrual` applies to `accrual` — the blueprint note says "reusing the SAME
     shared pooling primitives," which argues for yes (consistency), but it is not spelled out
     letter-by-letter. Make the call, log it.
- **Budget history**: iterations 6 and 7 both breached the 3600s wall-clock budget under full
  depth (iter-7 elapsed 6581s) and were demoted to lean. This iteration is deliberately narrow —
  one journey plus two small, already-root-caused riders — specifically to reduce that
  recurrence risk. Stay inside this scope; do not opportunistically pull in J-08/J-09 work.
- **Required-still-passing**: J-01 through J-06 and J-10 must stay green (deterministic replay +
  LLM fallback where no golden exists yet). J-07 has no golden replay script yet — expect one to
  be freshly authored this iteration by the browser-QA stage.
- **Anti-goal tripwires specific to this iteration**: the historical atlas must never be counted
  as confirmatory (the `discovery` block is explicitly labeled exploratory, never fed into
  `accrual`); the BH denominator machinery is untouched by this iteration's scope; the
  registration write path must stay generic (TC-9) — resist any temptation to special-case or
  hard-code the five shortlist candidates into the POST route itself.
