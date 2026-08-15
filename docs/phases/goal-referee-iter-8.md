# Goal Iteration 8 — The starter family: shortlist, registration, and two write-side fixes

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior iteration's verdict was ESCALATE (mandatory, no exceptions per the
  evaluator's own binding depth recommendation for this iteration)
- **Frontend Present:** yes
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-10
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **No confirmatory claim outside the gauntlet.** A confirmatory verdict exists only for a
    registered hypothesis with an immutable pre-data boundary, a calibrated randomization p, a
    family BH pass at the registered q, session-clustered robustness, and floors met — and
    exactly ONE confirmatory checkpoint per hypothesis, recorded as an append-only snapshot that
    later evaluations can never change (a replication is a new registered hypothesis).
    *(critical)*
  - **The historical atlas is exploratory forever.** No historical observation is ever served,
    labeled, or counted as forward confirmation; discovery data renders only under its
    exploratory label. *(critical)*
  - **Never shrink the BH denominator.** No BH pass may run with m smaller than the family's
    registered planned count; no candidate joins a family retroactively; no unevaluated or
    late-withdrawn candidate is dropped from m — they fold as p=1, never disappear; no family's
    q changes after registration. *(critical)*
  - **No gate loosens mid-era.** q, floors, targets, K, B, and every eligibility rule are fixed
    at registration; `insufficient_sample` is an answer, never a reason to widen anything.
    *(critical)*
  - **No confirmatory output without a verified oracle attestation.** The adjudication fold
    never serves a confirmatory verdict from an evaluation whose attestation is missing,
    mismatched, or version-stale — it serves the refusal state with its reason; descriptive
    output never masquerades as confirmatory. *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R,
    n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language,
    no imperative trading cues. *(critical)*

## GOAL

The operator can open `/desk`, see the Referee's five pre-registered candidate questions with
live sample-size readiness and rationale, and register one through an explicit confirm step that
writes a permanent, boundary-stamped hypothesis — the first real, browser-usable Referee action
this era.

## BACKGROUND

Iteration 7 shipped J-06 (estimand engines + adjudication) but was demoted from full to lean by
a wall-clock budget breach (elapsed 6581s vs the 3600s budget for both iter-6 and iter-7), so the
evaluator's own hard-audit pass — the one that has caught a critical finding in each of the last
two full iterations it actually ran — did not run against this era's most permanent write
machinery. The evaluator escalated for exactly that reason and its own probe (not the pipeline)
found two more gaps, both folded into this iteration as riders per its explicit recommendation.
Per the priority rubric: no journey regressed (rule 1); the last coherence verdict was
COHERENCE-WARN, not FAIL, so no mandatory consolidation pass is owed (rule 2) — its one advisory
(the stale `blueprint.md` registry-response doc) is fixed directly in this iteration's blueprint
edit, a doc-only change, no code; J-07 is the clearest unblocker (rule 3) — it is the first real
Referee UI surface and the dependency root of J-08/J-09; and it is deliberately targeted ALONE
(rule 6) because it is the single riskiest journey remaining this era — the first frontend touch
of the whole era, and the first UI path that performs a genuine permanent write.

**Depth is full because the prior verdict was ESCALATE** — binding, no exceptions, matching the
dispatch prompt's own instruction. Given the iter-6/iter-7 budget-breach history, this iteration
stays deliberately narrow (one journey plus two small, already-diagnosed riders) rather than
widening scope, to reduce the same time-pressure risk that caused the last two demotions.

**Lessons applied** (from `state/lessons.md`): iter-6's lesson — a guard on one field is
worthless if a sibling field reaches the same derived value another way — means the new
`discovery` fold must read the hypothesis's already-hardened `confirmation_start_boundary` field
verbatim and never accept or re-derive a boundary from any request input. iter-7's lesson — an
append-only store's WRITE side needs the same gate as its READ side, and an integrity-disclosure
fix belongs on EVERY reader of a store, not just the one an audit happened to name — is exactly
Riders 1 and 2 below (the write-side attestation gate, and extending `GET /adjudications` with
the same `integrity_errors` disclosure `GET /registry` already has).

Three riders ride inside this iteration rather than becoming their own (per iteration 7's
evaluator recommendation, all diagnosed by the evaluator's own probe, none of them new scope):

1. A failed oracle attestation must not mint the hypothesis's one permanent checkpoint snapshot
   as `corroborated` — gate the write, not just the read.
2. A corrupted hypothesis file must be surfaced on `GET /adjudications`, not silently dropped —
   the same fix Rider 2 of iteration 7 already applied to `GET /registry`.
3. The `blueprint.md` stale-documentation slip is fixed in this iteration's own blueprint edit
   (done already, alongside writing this spec — see the `state/blueprint.md` iter-8 note).

## IN SCOPE

### Backend
- [ ] `referee_registry.py`: a new starter-family shortlist fold (spec §7 S-1..S-5, module
  constants) computing LIVE readiness per candidate — reusing
  `referee_evidence.playbook_occurrence_readiness()`'s existing per-`(setup_id, side)` pooling
  for the three estimand-A candidates (S-1/S-2/S-3) and the existing band-context/backing-bucket
  resolution (already imported elsewhere this era) for the two `at_wall`-context candidates
  (S-4/S-5) — never a second pooling implementation.
- [ ] New `GET /research/desk/referee/registry/shortlist` route in `referee_routes.py` serving
  that fold (a plain read; GET never computes, T-8).
- [ ] `referee_registry.py`: extend each hypothesis entry already served by
  `GET /research/desk/referee/registry` with a read-side `discovery` block (pre-boundary
  observations in the hypothesis's own cell), reusing `_hypothesis_accrual`'s existing pooling
  and its already-hardened `confirmation_start_boundary` field — never contributing to the
  existing `accrual` block.
- [ ] Rider 1: `referee_adjudicate.py` — gate `run_evaluation_and_record`'s `role` decision on
  `attestation["passed"]`, so a failed oracle attestation records the evaluation as `"pending"`
  and never mints a hypothesis's one permanent checkpoint snapshot.
- [ ] Rider 2: `referee_adjudicate.py`'s `adjudications_response()` — surface
  `hypothesis_store.list()`'s integrity errors the same way `GET /registry` already does
  (a new `integrity_errors` key), instead of silently dropping a corrupted record.
- [ ] Extend `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` with every new served
  referee numeric this iteration adds (shortlist readiness numbers, the `discovery` block), with
  seeded counter-tests (standing guard-extension discipline).

### Frontend
- [ ] `apps/frontend/app/desk/page.tsx`: new **Referee Registry** `CollapsibleSection` (the
  first Referee UI slice), rendered below every shipped section, new `data-testid`s only (T-11)
  — the shortlist table (5 candidates, readiness numbers, rationale sentences), a selection +
  explicit confirmation step, POST to the existing `POST /registry/hypotheses` act.
- [ ] Render the registered-hypothesis row after a successful registration: boundary, target,
  `origin: historical-exploration`.
- [ ] Render the `discovery (exploratory)` label on a registered hypothesis's historical
  numbers, visibly distinct from its `accrual` numbers.
- [ ] Honest `"No hypotheses registered."` empty state when the registry has zero hypotheses.
- [ ] `lib/api.ts`/`lib/types.ts`: additions for the new shortlist GET and the extended registry
  GET shape, in the established style.

### New user-facing capability
The operator can, for the first time, see the Referee's five pre-registered candidate research
questions with live sample-size readiness and register one directly from `/desk`, producing a
permanent, boundary-stamped hypothesis.

### New information displayed
The five spec-pinned shortlist candidates (estimand, setup/side, primary measure/horizon,
rationale, live n/n_sessions/accrual-rate/projected-days-to-target); after registration, that
hypothesis's boundary date, target session count, and `historical-exploration` origin; the
`discovery (exploratory)` label on a registered hypothesis's pre-boundary historical numbers.

### New user actions
Select a shortlist candidate, review its live readiness, complete an explicit confirmation step,
submit the registration.

### UI surface changes
A new **Referee Registry** `CollapsibleSection` on `/desk`, rendered below every shipped
section. No existing section, column, or behavior changes.

### Product surface delta
`/desk` gains its first Referee-era visible feature; the Referee stops being purely
backend/keyless machinery and becomes something the operator can actually see and act on in the
browser.

### Blueprint conformance
`/desk` → **Referee Registry**, exactly the home `state/blueprint.md`'s Information Architecture
table already registers for J-07 ("shortlist sits above the registered-hypotheses table"). No
nav-skeleton change; no new route.

### Data-contract additions
1. **Starter-family shortlist** — NEW endpoint `GET /research/desk/referee/registry/shortlist`
   under the ALREADY-registered "Registry" row's owner (`referee_registry.py`; the row's
   endpoint cell is updated in `state/blueprint.md`, no new row). Response:
   `{candidates: [{candidate_id: "S-1".."S-5", estimand: "A"|"B"|"C", evidence_family:
   "playbook", setup_id: str, side: "long"|"short", context_predicate: dict|None,
   primary_measure_key: str, primary_horizon: str, sidedness: "greater"|"less"|"two-sided",
   null_spec_id: str|None, test_spec_id: str, rationale: str, n: int >= 0, n_sessions: int >= 0,
   target_sessions: int, min_occurrences: int, accrual_rate_sessions_per_day: float >= 0,
   projected_days_to_target: float|None (None when accrual_rate is 0)}, ...]}`. Full field-level
   detail registered in `state/blueprint.md`'s iter-8 note.
2. **`discovery` block** — a FIELD ADDITION on the already-registered "Registry" row's existing
   hypothesis entries (owner/endpoint unchanged): `discovery: {n: int >= 0, n_sessions: int >=
   0, label: "discovery (exploratory)"}`, computed by `referee_registry.py`, served on
   `GET /research/desk/referee/registry`. Registered in `state/blueprint.md`'s iter-8 note.

Both additions are registered in `runs/goal-session-referee/state/blueprint.md` as of this
iteration's spec-writing pass (the iter-8 note), alongside the doc-only fix to the stale
4-key-vs-5-key registry-response note the iter-7 coherence audit flagged.

## OUT OF SCOPE

- J-08 (strategy family + promotion interlock) and J-09 (full three-section `/desk` build-out —
  Referee Adjudications, Referee Runs sections; withdrawal-state display; MCP contract v5) —
  separate journeys, not touched this iteration.
- The real production registration of the operator's actual 2–3 approved hypotheses. Optional
  and operator-gated this iteration, matching goal.md's own J-07 acceptance text verbatim ("OR
  the honest not-yet-acted state is reported — never faked"). Do not fabricate a registration to
  satisfy DEFINITION OF DONE; the fixture-rig browser pass is what DoD requires.
- Any change to `desk_forward.py`, `desk_playbook*.py`, `levels.py`, `tradability.py`,
  `pnl_scan.py`, or `app/config.py` — frozen this whole era.
- Any threshold or definition change to the five shortlist candidates themselves — spec §7 is
  pinned verbatim (T-1); this iteration serves live readiness numbers around a fixed candidate
  list, it does not choose, tune, or rank candidates.
- Card 6.4 forming-bar fix, any new detector/setup, any new vendor or runtime dependency — all
  explicit Non-Goals of `docs/goal.md`.
- New `Config` fields — zero expected; the fingerprint pin `08e471b10130e1e2` must not move.

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa-agent: the shortlist renders with readiness numbers and
  rationale (screenshot); a fixture registration flows through confirmation to a recorded
  hypothesis whose row shows boundary, target, and `origin: historical-exploration`
  (screenshot); the `discovery (exploratory)` label renders on historical numbers (screenshot).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-06, J-10 remain green
  (deterministic replay + LLM fallback, mechanically verified).
- [ ] No anti-goal violation introduced: historical atlas never counted as confirmatory; BH
  denominator untouched; the registration write path stays generic (never restricted to the
  five shortlist candidates).
- [ ] Rider 1 verified: a fixture evaluation with a deliberately failed oracle attestation never
  records `role: "checkpoint"` and never writes an adjudication snapshot.
- [ ] Rider 2 verified: a corrupted hypothesis file is surfaced in
  `GET /research/desk/referee/adjudications`'s `integrity_errors`, not silently dropped.
- [ ] Unit tests pass; suite collected count >= 2,642, 0 failed; no regressions.
- [ ] `Config().config_fingerprint()` prints `08e471b10130e1e2`; MCP tool count stays 20 (J-09's
  job to grow it to 22 — unchanged this iteration).
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-8-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (first real pass — no golden script exists yet for it); required-still-passing
  replay/verify for J-01, J-02, J-03, J-04, J-05, J-06, J-10 (J-10 via its own golden script;
  the rest via deterministic replay where a golden exists, else LLM browser-qa live-endpoint
  smoke, per `state/lessons.md` iter-1).
- Unit/integration: the shortlist fold (readiness numbers, zero-corpus candidates, the
  divide-by-zero guard on `projected_days_to_target`); the `discovery` fold (boundary counter-
  test); Rider 1 (failed-attestation write gate); Rider 2 (corrupted-file disclosure on
  `GET /adjudications`); the registration write path's genericity (a non-shortlist payload still
  registers).
- Error cases: a malformed shortlist read must never 500 on an empty registry or empty playbook
  store (honest empty candidates never crashes); a corrupted hypothesis file must be disclosed,
  never crash the endpoint that reads it; `projected_days_to_target` must never divide by zero.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above
maps to at least one concrete scenario line below.

- TC-1: given the fixture playbook store's recorded signals, when `GET
  /research/desk/referee/registry/shortlist` is called, then the response's `candidates` array
  has exactly 5 entries with `candidate_id` values `S-1`..`S-5`, each carrying a non-negative
  `n`, `n_sessions`, `accrual_rate_sessions_per_day`, `target_sessions`, and `min_occurrences`.
- TC-2: given a fixture playbook store with zero recorded `jbe:long` signals, when the shortlist
  endpoint is called, then candidate `S-2` (jbe:long, estimand A) is served with `n: 0`,
  `n_sessions: 0`, `accrual_rate_sessions_per_day: 0`, and `projected_days_to_target: null` —
  never a divide-by-zero value.
- TC-3: given the operator opens `/desk`'s Referee Registry section on the QA fixture rig, when
  the section expands, then the shortlist table renders 5 rows, each with its rationale sentence
  and readiness numbers, and a screenshot is captured.
- TC-4: given the operator selects candidate S-4 and completes the confirmation step in the
  browser, when the confirm action is submitted, then `POST /research/desk/referee/registry/
  hypotheses` is called with `confirm: true`, the response carries a `hypothesis_id`, and the
  returned hypothesis's `confirmation_start_boundary`, `target_sessions`, and `origin:
  "historical-exploration"` render in the registered-hypotheses row, evidenced by a screenshot.
- TC-5: given a hypothesis registered in TC-4 with pre-boundary historical signals on file for
  its `(setup_id, side)` cell, when its registry row is viewed, then a `discovery (exploratory)`
  label renders beside its historical count, that count is served in a `discovery` block
  distinct from `accrual`, and a screenshot is captured.
- TC-6: given no operator action has been taken on the real production registry, when `GET
  /research/desk/referee/registry/shortlist` and `GET /research/desk/referee/registry` are
  called against the real store, then the shortlist is served with 5 candidates and
  `hypotheses: []` — the honest not-yet-acted state, never a fabricated registration.
- TC-7: given an evaluation whose `run_oracle_attestation()` returns `passed: false`, when
  `run_evaluation_and_record` is called, then the stored evaluation record's `role` is
  `"pending"` (never `"checkpoint"`), and no adjudication snapshot is written for that
  hypothesis.
- TC-8: given a hypothesis store file on disk that is corrupted (unparseable JSON) alongside an
  existing hypothesis with a checkpoint snapshot, when `GET
  /research/desk/referee/adjudications` is called, then the response's `integrity_errors` array
  names the corrupted file instead of the endpoint silently omitting it.
- TC-9: given the registration write path (`POST /registry/hypotheses`), when a hypothesis
  payload for a setup/side combination NOT among S-1..S-5 (e.g. `dbi:short`, estimand A) is
  submitted with `confirm: true`, then it registers successfully (HTTP 200/201) — proving the
  write path accepts any valid hypothesis, never only the five shortlist candidates.
- TC-10: given a deep-backfilled playbook record for a `session_date` before a hypothesis's
  `confirmation_start_boundary`, recorded (written to disk) after registration, when the
  discovery/accrual fold runs, then that record's `session_date` contributes to
  `discovery.n_sessions`, never to `accrual.informative_post_boundary_sessions` — proving
  `session_date`, not `recorded_at`, gates the boundary.
- TC-11: given the full backend suite, when it is run, then the collected count is >= 2,642, 0
  tests fail, and `Config().config_fingerprint()` prints `08e471b10130e1e2`.
- TC-12: given the kept `/desk` product (screen history, forward returns, refresh chain,
  briefing, all Playbook sections), when walked in a real browser after `rm -rf
  apps/frontend/.next` and a rebuild, then every shipped section renders exactly as shipped
  alongside the new Referee Registry section, each evidenced by a screenshot.

## NOTES

- **Human-owned, non-blocking, outside this project** (carried since iteration 2): the unrelated
  trendora backend on port 8255 has not been restarted. No action needed from this session.
- **Budget history:** iterations 6 and 7 both breached the 3600s wall-clock budget under full
  depth (iter-7 elapsed 6581s) and were trimmed to lean with `DEFERRED-BUDGET` rows. This
  iteration is deliberately narrow (one journey, two small riders, both already root-caused by
  the evaluator) to reduce recurrence risk, but depth itself stays full — non-negotiable given
  the prior ESCALATE.
- **`blueprint.md` maintenance done alongside this spec:** the iter-7 coherence-auditor's
  advisory (stale 4-key-vs-5-key `GET /registry` doc note, and the false claim in
  `docs/handoffs/goal-referee-iter-7-dev.md` that it had already been fixed) is corrected in
  `state/blueprint.md`'s new iter-8 note — a doc-only change, no code, already applied before
  this spec was written.
- **Assumption logged:** `state/assumptions.md`'s iter-8 entry records the reading of "no
  hard-coded hypothesis set" as governing the registration WRITE PATH's genericity (TC-9), not
  the shortlist's own spec-pinned S-1..S-5 candidate definitions (which are module constants by
  design, per T-1 and the Parameters discipline).
- **Golden replay:** J-07 is the first browser-verifiable Referee journey; expect its golden
  script to be freshly created this iteration (none exists yet), while J-01–J-06 stay on the
  keyless-automated + replay/live-smoke pattern per `state/lessons.md` iter-1.
