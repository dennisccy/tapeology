# goal-referee-iter-8 Dev Handoff

**Phase:** goal-referee-iter-8
**Date:** 2026-08-15
**Agent:** developer
**Status:** complete

## What Was Built

- **The starter-family shortlist fold** (`referee_registry.shortlist_response`, new
  `GET /research/desk/referee/registry/shortlist`): spec §7's five pinned candidates (S-1..S-5,
  module constants) beside LIVE readiness — `n`/`n_sessions` for S-1..S-3 (estimand A) reuse
  `playbook_occurrence_readiness()`'s existing `per_setup_side` pooling verbatim; S-4/S-5
  (`at_wall` context) reuse a new `_starter_context_readiness()` helper that walks the same
  current-basis newest-per-date raw-record set and resolves each matching signal's own backing
  bucket through `referee_null.resolve_occurrence_backing_bucket` over a `compute=False`
  `BandMapResolver` (a recorded-band-map lookup, never a fresh compute). A new
  `_corpus_session_span_days()` helper (earliest-to-latest recorded `session_date`, inclusive)
  is the shared denominator for `accrual_rate_sessions_per_day`; `projected_days_to_target`
  reads `null` when the rate is `0` — never a divide-by-zero value.
  *(Corrected by the iter-8 audit, finding B2: `projected_days_to_target` was
  `max(0.0, (target_sessions - n_sessions) / rate)`, which served `0.0` — "ready now" — for every
  candidate whose historical cell already met the target, i.e. all three estimand-A candidates
  against the operator's real corpus, where the honest waits are ~74/~119/~50 days. It is now
  `target_sessions / rate`, measured from zero, because `target_sessions` is a POST-boundary count
  and registering stamps the boundary at that instant. The `0.0` floor is gone with the
  subtraction; see `state/assumptions.md`'s iter-8 auditor entry.)*
- **The `discovery (exploratory)` fold** (`referee_registry._hypothesis_discovery`): a new field
  addition on every hypothesis entry `GET /research/desk/referee/registry` already serves —
  pre-boundary (`session_date <= confirmation_start_boundary`) occurrence/session counts in the
  hypothesis's own `(setup_id, side)` cell, reusing the exact same shared pooling primitives and
  current-basis filter `_hypothesis_accrual` already uses, with the boundary inequality inverted.
  Never contributes to `accrual`; a deep-backfilled pre-boundary record recorded after
  registration still lands in `discovery`, keyed on `session_date` alone, never `recorded_at`.
- **Rider 1** (write-side attestation gate, `referee_adjudicate.run_evaluation_and_record`): a
  failed oracle attestation (`attestation["passed"] is False`) now downgrades `fields["role"]`
  from `"checkpoint"` to `"pending"` immediately before the record is written, so the
  hypothesis's one permanent adjudication snapshot is never minted from an unattested
  evaluation. Only the checkpoint case is touched — "monitoring"/"pending" never wrote a
  snapshot regardless — and every other computed field (T, permutation_p, CIs, etc.) stays
  exactly as computed; only the permanent-write eligibility is gated.
- **Rider 2** (integrity disclosure parity, `referee_adjudicate.adjudications_response`): the
  function now surfaces `hypothesis_store.list()`'s own integrity errors as a new
  `integrity_errors` key on `GET /research/desk/referee/adjudications`, the same way
  `GET /research/desk/referee/registry` already does, instead of silently discarding them.
- **Guard extension** (`test_desk_ui_guards.py`): `_PRICE_ARITHMETIC_FIELDS` gains
  `candidate.(n|n_sessions|accrual_rate_sessions_per_day|projected_days_to_target)` and
  `hyp.discovery.(n|n_sessions)` — the exact new served referee numerics this iteration's JSX
  actually reads — plus a seeded counter-test proving the extended pattern fires on each new
  field and does not over-match the page's own "X / Y" display idiom.
- **Frontend — the first Referee UI slice**: a new **Referee Registry** `CollapsibleSection` on
  `/desk`, rendered below every shipped section (Playbook Evidence is now the second-to-last).
  The shortlist table (5 rows: candidate id, estimand, setup/side + context bucket, primary
  horizon, rationale, `n`, sessions, accrual rate/day, projected days, a Select action); a
  select → confirm → submit registration flow (a distinct confirmation panel between selection
  and submit, an inline honest error on 422/409); the registered-hypotheses table (hypothesis
  id, setup/side, boundary, origin, status, accrual, and the `discovery (exploratory)` label
  rendered visibly distinct from accrual — plain typographic text, never a colored badge); the
  honest `"No hypotheses registered."` empty state. First-ever `lib/api.ts`/`lib/types.ts`
  referee bindings (`fetchRefereeShortlist`, `fetchRefereeRegistry`,
  `postRefereeRegistryHypothesis`, and the full `Referee*` type family).

## Files Changed

- `apps/backend/app/research/referee_registry.py` -- adds `REFEREE_STARTER_FAMILY_SHORTLIST`
  (module constants), `_corpus_session_span_days`, `_starter_context_readiness`,
  `shortlist_response`, `_hypothesis_discovery`; wires `discovery` into `registry_response()`'s
  per-hypothesis fold; extends imports (`BandMapResolver`, `resolve_occurrence_backing_bucket`,
  `AT_WALL` from `.referee_null`; `BarStore`; `Config`; `date`).
- `apps/backend/app/research/referee_routes.py` -- new `GET /registry/shortlist` route wired to
  `shortlist_response`, mirroring the existing `GET /registry` route's dependency-injection
  style.
- `apps/backend/app/research/referee_adjudicate.py` -- Rider 1 (the write-side attestation gate
  in `run_evaluation_and_record`) and Rider 2 (`integrity_errors` on `adjudications_response`).
- `apps/backend/tests/test_referee_registry.py` -- shortlist fold tests (TC-1, TC-2, the
  divide-by-zero-floor counter-test), a `bar_store` fixture, discovery-fold assertions added to
  the existing accrual test, a non-vacuous `_starter_context_readiness` discrimination test, an
  end-to-end shortlist wiring test (monkeypatched `BandMapResolver`), a route-level TC-6 test,
  TC-9 (non-shortlist write-path genericity), TC-10 (deep-backfilled/on-boundary discovery vs.
  accrual boundary test).
- `apps/backend/tests/test_referee_adjudicate.py` -- Rider 1 tests (forced failing attestation →
  `role: "pending"`, no snapshot; a can-fail counter-test with the real passing attestation),
  Rider 2 tests (corrupted hypothesis file surfaced in `/adjudications`'s `integrity_errors`; a
  route-level healthy-store companion).
- `apps/backend/tests/test_desk_ui_guards.py` -- extends `_PRICE_ARITHMETIC_FIELDS` with the new
  referee numerics; a new seeded counter-test.
- `apps/frontend/app/desk/page.tsx` -- `"refereeRegistry"` added to `DeskCollapsibleSection`;
  two new module constants (`REFEREE_STARTER_FAMILY_ID`, `REFEREE_STARTER_FAMILY_Q`); new state
  (`refereeShortlistResult`, `refereeRegistryResult`, selection/registering/error state); a new
  `toggleSection` branch (deferred fetch, no new effect); `handleRegisterRefereeCandidate` (a
  plain async handler); the new `<section aria-label="Referee Registry">` block; the
  `RefereeRegistrySection` and `RefereeHypothesesTable` components.
- `apps/frontend/lib/api.ts` -- `fetchRefereeShortlist`, `fetchRefereeRegistry`,
  `postRefereeRegistryHypothesis`.
- `apps/frontend/lib/types.ts` -- the full `Referee*` type family (`RefereeShortlistCandidate`,
  `RefereeShortlistResponse`, `RefereeAccrual`, `RefereeDiscovery`, `RefereeHypothesis`,
  `RefereeFamily`, `RefereeWithdrawal`, `RefereeIntegrityError`, `RefereeRegistryResponse`,
  `RefereeHypothesisRegistrationPayload`).
- `runs/goal-session-referee/state/assumptions.md` -- two new iter-8 developer entries (the
  `accrual_rate_sessions_per_day`/`projected_days_to_target` formula choice; the discovery fold
  applying the same stale-basis exclusion as accrual).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ --junit-xml=<path>`
Result: 2655 collected, 0 failed, 0 errors, 8 skipped (>= the 2,642 DoD floor).

Also independently verified:
- `Config().config_fingerprint()` prints `08e471b10130e1e2` (unchanged).
- `tests/test_mcp_server.py::EXPECTED_TOOLS` still has exactly 20 entries (unchanged this
  iteration — J-09's job to grow it).
- `tests/test_desk_refresh_chain_guard.py::_EXPECTED_EFFECT_COUNT` (19) unchanged — zero new
  `useEffect` calls were added; the new section's reads are wired through the existing
  `toggleSection` deferred-fetch handler, and registration is a plain async `onClick` handler.
- `tests/test_copy_discipline.py` green — the new frontend copy (rationale sentences, table
  labels, the confirm-step sentence, the empty state) carries no imperative/predictive/claim
  language.
- `tests/test_referee_guards.py` green — the new `BandMapResolver`/`resolve_occurrence_
  backing_bucket`/`AT_WALL` imports in `referee_registry.py` are transitive (`from .referee_null
  import ...`), never a direct `desk_playbook_context` import; the import-topology guard still
  passes with `referee_null.py` as the sole sanctioned exception.
- `apps/frontend`: `node_modules/.bin/tsc --noEmit -p tsconfig.json` — exit code 0, zero
  TypeScript errors.

## Known Issues

- **The real production 2–3 registrations were not made this iteration.** Per goal.md's own
  J-07 acceptance text ("OR the honest not-yet-acted state is reported — never faked") and the
  phase spec's OUT OF SCOPE list, this is explicitly optional and operator-gated. Verified
  against the real (ambient) backend store: `GET .../registry/shortlist` serves all 5 candidates
  and `GET .../registry` serves `hypotheses: []` — the honest not-yet-acted state.
- **Browser verification (TC-3/TC-4/TC-5/TC-12) was not run by this agent.** That is the
  browser-qa-agent's job in the pipeline, not the developer's. I did verify the backend routes
  and the frontend TypeScript compile cleanly end-to-end, and did a manual `curl` smoke test of
  both `GET /research/desk/referee/registry/shortlist` (returns S-1..S-5) and
  `GET /research/desk/referee/registry` (returns the honest empty state) against a live
  `scripts/dev.sh`-started backend/frontend pair, plus confirmed the `/desk` page itself returns
  200. I did not drive a real browser through the select → confirm → submit flow myself.
- **No `min_occurrences`/`target_sessions` column is rendered in the shortlist table.** Both are
  served by the backend (TC-1 requires them, and they are exercised there) but the frontend only
  surfaces the four readiness numbers goal.md's own J-07 Step 1 names in prose (`n`,
  `n_sessions`, accrual rate, projected days) — `target_sessions` is folded into "projected days
  to target" rather than shown as its own column, and `min_occurrences` is not displayed at all.
  This was a deliberate scope-minimization call (fewer table columns, matching exactly what the
  acceptance text names), not an oversight; both fields remain in the served JSON for any future
  UI that wants them.
- **The "already registered" state on a shortlist row is inferred client-side** (comparing
  `candidate_id` against the fetched registry's `hypothesis_id`s) rather than served as a
  dedicated backend field. This is a plain equality/membership check, not arithmetic derivation
  of a numeric value, so it does not fall under the price-arithmetic guard's scope; if the
  operator selects an already-registered candidate anyway (e.g. a stale client view), the
  backend's own 409 refusal is surfaced as the honest inline error.

## Pre-handoff verification

- Service startup: `scripts/dev.sh` started cleanly on :8301 (backend) / :3301 (frontend), both
  reachable (curl 200), then stopped by exact PID and restarted cleanly a second time on the
  same ports with zero conflicts.
- No new native dependency or post-install step was introduced this iteration.
- No live external-API integration was added this iteration (the S-4/S-5 band-context lookup
  reads the already-recorded, already-tested tradability cache — no new adapter).
