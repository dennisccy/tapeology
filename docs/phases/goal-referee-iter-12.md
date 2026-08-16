# Goal Iteration 12 — The accrual projection states its own basis

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 12
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-11
- **Required-still-passing journeys:** J-05, J-07, J-09, J-10
- **Anti-goal reminders:**
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R,
    n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language,
    no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **The Referee never feeds back.** No referee output gates, filters, ranks, or tunes any
    detector, context, screen, or strategy computation (import-ban + source-scan
    guard-tested); the frozen research vocabulary stays frozen. *(critical)*
  - **No confirmatory claim outside the gauntlet.** A confirmatory verdict exists only for a
    registered hypothesis with an immutable pre-data boundary, a calibrated randomization p, a
    family BH pass at the registered q, session-clustered robustness, and floors met — and
    exactly ONE confirmatory checkpoint per hypothesis, recorded as an append-only snapshot
    that later evaluations can never change (a replication is a new registered hypothesis).
    *(critical)*

## GOAL

Serve and render a corpus-honest accrual disclosure — one `accrual_basis` block (recorded vs.
pooled session counts, corpus span, and the longest zero-session recording gap) plus two new
per-candidate rate/projection fields, computed once inside the existing starter-family shortlist
fold and shown beside — never replacing — the shipped calendar-day accrual numbers on `/desk`'s
Referee Registry section, so the owner sees the wait measured in actually-recorded sessions
before taking the one irreversible act this era gates behind sample size.

## BACKGROUND

Era 6 closed `GOAL_ACHIEVED` at iteration 11 (two-key confirmed): all ten Must-have journeys held
current evidence, zero open anti-goal violations, empty product diff. The goal-proposer then
appended exactly one new journey, J-11, inside `docs/goal.md`'s `AUTO:journeys` marker block: the
shipped shortlist's `accrual_rate_sessions_per_day` / `projected_days_to_target` divide by the
corpus's raw calendar-day span (`_corpus_session_span_days`), which silently includes stretches
with zero recorded trading sessions — a multi-month recording gap inflates the projected wait
before the owner registers a hypothesis, the one act this era makes immutable at the instant it
happens (J-05's `RetroactiveBoundary` law). J-11 is deliberately narrow and read-side: it adds no
`Config` field, no `referee_parameters()` entry, and feeds no null/test/BH/verdict/gate — every
input it needs is already in scope inside `shortlist_response()`'s existing single store scan
(`playbook_store.list()` → `newest_by_date`) plus the already-imported
`playbook_occurrence_readiness()` fold's `distinct_sessions`/`stale_basis_dates`.

Depth follows the evaluator's binding `lean` recommendation; no escape condition holds — the
prior verdict was `GOAL_ACHIEVED` (not ESCALATE/REGRESSION), the prior coherence verdict was
`COHERENCE-PASS` (not FAIL), only 1 of the 6-iteration hardening cadence has elapsed, and while
J-11 is nominally "never-implemented, backend + frontend, with a real Data-contract addition,"
its blast radius names in one sentence — one function's output shape
(`referee_registry.py::shortlist_response()`) rendered as one line plus one column inside one
already-shipped section (Referee Registry). Lean's own definition explicitly includes "a new
endpoint plus its UI use"; this is narrower still (new fields on an *already-registered*
endpoint, no new route, no new section). goal.md's own J-11 text reinforces this scoping
repeatedly ("never a second `PlaybookStore.list()`", "zero new Config fields, zero new referee
constants, and NO entry in `referee_parameters()`"), and this session's own `lessons.md` (iter-9's
second lesson) records that the engine's arbiter only auto-grants full depth when the prior
*verdict* itself was ESCALATE — requesting full here would only be demoted.

Two lessons applied from `lessons.md`: iter-8's finding that "any served number whose formula has
a subtraction, a floor, or a saturation point must be hand-checked against REAL-corpus
magnitudes" (the shipped `projected_days_to_target` had exactly this class of bug, caught only by
hand-checking real magnitudes) — TC-4/TC-5 below require hand-computed fixture numbers, and the
dev handoff should record whether the new fields were sanity-checked against the real 210-record
corpus's own known gap. iter-8's sibling caution about a "complement/mirror of an existing fold"
silently dropping a filter its neighbour applies: the new `informative_sessions_per_pooled_session`
field must divide each candidate's own ALREADY-context-filtered `n_sessions` — the exact value the
existing loop already computed for that candidate (`_starter_context_readiness`'s filtered count
for S-4/S-5/S-6, the unfiltered `per_setup_side` count for S-1/S-2/S-3) — by the corpus-wide
`pooled_sessions_at_current_basis`, never a fresh or differently-filtered recomputation of either
operand. iter-10's evidence lesson (checksum every distinct on-screen state, since two clauses
sharing one screenshot file has hidden a missing acceptance before) applies directly to
TC-12/TC-13/TC-14, since this journey's own acceptance text names several different on-screen
states inside the same browser pass.

Target selection: J-11 is the only Target journey because it is the only journey with open scope
this iteration — no journey is regressed, the last coherence audit was a PASS (nothing to
consolidate), and J-11 unblocks nothing else but is itself the era's entire remaining backlog.
Rule 5 (never bundle two risky journeys) is moot with a single target. The four non-blocking
hardening items and the walkthrough-recorder tooling gap carried in `iteration-state.md`'s "Do
not redo" list are deliberately NOT folded in even though a developer will be "in this area" —
none of the four lives inside `referee_registry.py` or the Referee Registry section (they touch
`referee_adjudicate.py`, the store-scope guard script, and an unrelated fetch-failure code path),
so bundling them would widen this iteration's blast radius past "one sentence" for no acceptance
benefit; they remain hardening for whichever future iteration actually touches those files.

## IN SCOPE

### Backend

- [ ] `apps/backend/app/research/referee_registry.py::shortlist_response()` — add the
  `accrual_basis` block and the two new per-candidate fields specified in Data-contract additions
  below, computed from data the function's existing single store scan already holds (no second
  `PlaybookStore.list()`, no second pooling walk, no new `BandMapResolver` compute).
- [ ] Add a small helper (e.g. `_longest_zero_session_stretch(newest_by_date)`) that walks the
  SAME sorted date keys `shortlist_response()` already builds to find the longest gap between two
  consecutive recorded session dates, returning its length and the two bounding dates.
- [ ] Zero new `Config` fields; zero new `referee_parameters()` entries. Add/extend a unit test
  that asserts `referee_parameters()`'s served JSON is unchanged after this iteration.
- [ ] `docs/referee-statistical-spec.md` §9 — append one dated, named addendum paragraph stating
  the accrual projection is a read-side planning disclosure no statistical procedure consumes,
  and that both bases (calendar-day and recorded-session) are served side by side.
- [ ] Extend `tests/test_desk_ui_guards.py::_PRICE_ARITHMETIC_FIELDS` with every new served
  numeric plus its seeded counter-test, in the established referee shape.
- [ ] Extend `tests/test_copy_discipline.py` coverage for any new copy strings introduced by the
  basis line / new column (descriptive statistics only).

### Frontend

- [ ] `apps/frontend/app/desk/page.tsx::RefereeRegistrySection()` — render one descriptive basis
  line (recorded sessions, pooled sessions, span days, first → last session date, longest
  zero-session stretch with its bounding dates) above the shipped `<table
  data-testid="referee-shortlist-table">`, reading `shortlist.accrual_basis` verbatim — zero
  client-side arithmetic.
- [ ] Add exactly one new right-aligned `<th>`/`<td>` column immediately beside the shipped
  "Projected days" column, rendering `candidate.projected_pooled_sessions_to_target`
  (`toFixed(0)`, or "—" when `null`, mirroring the shipped `projected_days_to_target` rendering
  convention exactly). New `data-testid`s only; no shipped column, heading, or `data-testid`
  touched.
- [ ] Do not add a dedicated column for `informative_sessions_per_pooled_session` this iteration
  (see `state/assumptions.md` iter-12 entry) — the field is served on the API response and
  exercised by its own backend test.

### New user-facing capability

The owner reads, directly beside each starter-family candidate's existing calendar-day "days to
target" projection, how many sessions the corpus has actually recorded (not raw calendar days)
and a projected wait measured in recorded sessions — so a multi-month recording gap in the corpus
no longer silently inflates the estimated wait before an irreversible registration.

### New information displayed

- One basis line above the shortlist table: recorded sessions, pooled sessions at the current
  detector basis, corpus span in days, first → last recorded session date, and the longest
  zero-session stretch (length plus its two bounding dates).
- One new column per shortlist candidate: the recorded-session-based projected wait, alongside
  the existing calendar-day projection.

### New user actions

None. This is a pure read-side rendering addition — no new buttons, forms, or controls; the
existing registration action (`Select` → confirm) is untouched.

### UI surface changes

`/desk` → Referee Registry section only: one new line above the shortlist table, one new column
inside it. No new page, no new section, no new nav entry.

### Product surface delta

The already-shipped Referee Registry section gains a denser, honester accrual disclosure beside
its existing numbers. No new route or section header.

### Blueprint conformance

Lives entirely under the Desk → **Referee Registry** home already registered in
`runs/goal-session-referee/state/blueprint.md`'s Information Architecture table (the J-05/J-07
row) — no new IA entry needed.

### Data-contract additions

Field-level additions to the ALREADY-registered "Registry (families, hypotheses, withdrawals,
certificates)" Data Contract row — owner `referee_registry.py`, endpoint
`GET /research/desk/referee/registry/shortlist` (endpoint cell already registered at iter-8; this
iteration adds no new row, no new endpoint, no owner change):

- New top-level response key `accrual_basis`: `{corpus_first_session_date: str ("YYYY-MM-DD"),
  corpus_last_session_date: str ("YYYY-MM-DD"), corpus_span_days: int >= 0 (byte-identical to the
  existing `_corpus_session_span_days()` output already used by the shipped
  `accrual_rate_sessions_per_day` — reused, never recomputed), recorded_sessions_in_span: int >= 0
  (== `playbook_occurrence_readiness()`'s own `distinct_sessions`), pooled_sessions_at_current_basis:
  int >= 0 (== that same `distinct_sessions` minus the count of dates in that fold's own
  `stale_basis_dates`), longest_zero_session_stretch_days: int >= 0,
  longest_zero_session_stretch_start: str ("YYYY-MM-DD"), longest_zero_session_stretch_end: str
  ("YYYY-MM-DD")}`.
- Two new fields on each existing `candidates[]` entry, beside — never replacing — the shipped
  `accrual_rate_sessions_per_day` / `projected_days_to_target`:
  `informative_sessions_per_pooled_session: float >= 0` (that candidate's own already-computed
  `n_sessions` divided by `accrual_basis.pooled_sessions_at_current_basis`; `0.0` when the
  denominator is `0`, never a division error) and `projected_pooled_sessions_to_target: float |
  null` (`target_sessions` divided by that rate; `null` when the rate is `0`, reusing the shipped
  divide-by-zero discipline verbatim).

This iteration edits `runs/goal-session-referee/state/blueprint.md` to register these as an
iter-12 note under the existing Registry row (no new row, no IA change).

## OUT OF SCOPE

- Any change to J-04/J-06/J-08 (nulls, evaluation, adjudication, promotion) modules or their
  served fields — J-11 feeds no null, no test statistic, no p-value, no BH denominator, no
  verdict, no gate.
- Any new MCP tool — MCP stays exactly 22 tools; the shortlist subpath is not proxied by any tool
  today (`desk_referee_registry` proxies the whole-registry endpoint, not `/shortlist`) and this
  iteration adds none.
- Any change to the shipped `accrual_rate_sessions_per_day` / `projected_days_to_target` formulas
  — both must stay byte-identical (golden-verified, TC-6).
- Any new `Config` field, any `referee_parameters()` entry, any null/evaluation/adjudication/
  certificate identity change, any PnL-ledger write, any champion-pointer movement.
- A dedicated UI column for `informative_sessions_per_pooled_session` (see `state/assumptions.md`
  iter-12 entry) — API field only this iteration.
- The four non-blocking hardening items carried in `iteration-state.md`'s "Do not redo" list (4
  Referee dirs into the store-scope guard; both-names-unknown certificate matching in
  `referee_adjudicate.py:550`; dash-vs-unknown on a failed second fetch; the stale `19/7/1`
  comment) — none lives inside `referee_registry.py` or the Referee Registry section; they remain
  hardening for whichever future iteration actually touches those files.
- The shared walkthrough-recorder's missing `scroll` action support
  (`incredible_auto_dev/scripts/automation/lib/demo_runner.py`) — vendored framework tooling, not
  Tapeology product code (iter-11's own recorded assumption-ledger entry already ruled this out
  of a goal-decomposer's remit). J-11's own walkthrough is written using only the supported
  action vocabulary (`goto`/`click`/`fill`/`expect`/`wait_for`), so this limitation does not block
  J-11's acceptance.
- Committing prior iterations' uncommitted evidence files, and the unrelated trendora backend on
  port 8255 (down since iteration 2) — both human-owned, outside this project/iteration.

## DEFINITION OF DONE

- [ ] J-11 passes via browser-qa-agent — fresh T-9 clean-rebuild screenshots show the new basis
  line and new column in the Referee Registry section, and every other shipped `/desk` section
  renders exactly as shipped in the same pass
- [ ] Required-still-passing journeys J-05, J-07, J-09, J-10 remain green (deterministic replay
  where a golden script exists; LLM browser-qa fallback otherwise)
- [ ] No anti-goal violation introduced: zero new `Config` field, `referee_parameters()`
  byte-unchanged, `Config().config_fingerprint()` prints `08e471b10130e1e2`, zero diff to
  `desk_playbook*.py`/`desk_forward.py`/`levels.py`/`tradability.py`/`pnl_scan.py`, every
  previously recorded store file byte-identical (SHA-256 listing), PnL ledger + champion pointer
  byte-identical, `default`-profile equivalence green, MCP still exactly 22 tools
- [ ] Unit tests pass; no regressions — full backend suite green, collecting at least 2,688 tests
  (era-close baseline) with 0 failures
- [ ] `docs/referee-statistical-spec.md` §9 carries the dated addendum paragraph
- [ ] `[NEW]`-flagged demo-narrator walkthrough recorded using only `goto`/`click`/`fill`/
  `expect`/`wait_for`
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-12-dev.md`

## TESTING REQUIREMENTS

- Browser: J-11 (new basis line + new column in Referee Registry, every other shipped `/desk`
  section unchanged in the same pass); regression replay for J-05, J-07, J-09, J-10.
- Unit/integration: `referee_registry.py::shortlist_response()`'s new `accrual_basis` block and
  two per-candidate fields against a fixture corpus carrying a deliberate multi-month recording
  gap and a zero-pooled-session candidate; golden byte-identity of the shipped fields;
  two-run determinism; extended guard tests (`_PRICE_ARITHMETIC_FIELDS` + counter-tests,
  `test_copy_discipline.py`); `test_mcp_server.py::EXPECTED_TOOLS` stays at 22; full-suite
  regression.
- Error cases: empty corpus (`accrual_basis` fields all zero/empty, never a crash); zero
  pooled-session candidate (rate `0.0`, projection `null`, never a `ZeroDivisionError`); a
  corrupt/missing playbook record still surfaces through the existing `integrity_errors`
  discipline, never silently dropped.

Test-first contract:

- TC-1: given a fixture playbook corpus whose recorded session dates span 2026-01-05 to
  2026-06-20 with a deliberate zero-session gap from 2026-02-10 to 2026-04-15 inclusive, when
  `GET /research/desk/referee/registry/shortlist` is called, then `accrual_basis`'s
  `corpus_first_session_date` == "2026-01-05", `corpus_last_session_date` == "2026-06-20",
  `longest_zero_session_stretch_days` equals the hand-counted gap length, and
  `longest_zero_session_stretch_start`/`_end` equal the two recorded session dates immediately
  bounding that gap.
- TC-2: given the same fixture corpus, when the shortlist is served, then
  `accrual_basis.corpus_span_days` equals the value the shipped `accrual_rate_sessions_per_day`
  already divides by for that store (byte-identical to `_corpus_session_span_days()`'s existing
  output), `accrual_basis.recorded_sessions_in_span` equals `playbook_occurrence_readiness()`'s
  own `distinct_sessions` for that store, and `accrual_basis.pooled_sessions_at_current_basis`
  equals that same `distinct_sessions` minus the count of dates in that fold's own
  `stale_basis_dates`.
- TC-3: given a fixture candidate whose cell has zero occurrences pooled at the current detector
  basis, when the shortlist is served, then that candidate's `informative_sessions_per_pooled_session`
  is `0.0` (not a `ZeroDivisionError`) and `projected_pooled_sessions_to_target` is `null`; on
  `/desk`, the new column renders "—" for that row.
- TC-4: given a fixture candidate with a non-zero pooled-session rate, when the shortlist is
  served, then `informative_sessions_per_pooled_session` equals that candidate's own already-computed
  `n_sessions` divided by `accrual_basis.pooled_sessions_at_current_basis` exactly, and
  `projected_pooled_sessions_to_target` equals `target_sessions` divided by that rate exactly
  (hand-computed fixture numbers, not approximated).
- TC-5: given identical fixture stores, when `GET /research/desk/referee/registry/shortlist` is
  called twice in a row with no writes between calls, then the two response bodies (including
  every new field) are byte-identical.
- TC-6: given the same fixture stores before and after this iteration's change, when the shipped
  `accrual_rate_sessions_per_day` and `projected_days_to_target` fields are compared, then both
  are byte-identical to their pre-iteration (golden) values.
- TC-7: given a running backend, when `GET /research/desk/referee/registry/shortlist` is called,
  then a unit test proves the call performs exactly the one store scan (`playbook_store.list()`)
  `shortlist_response()` already performs today, with `BandMapResolver` still constructed with
  `compute=False`.
- TC-8: given `Config().config_fingerprint()` printed before and after this iteration's changes,
  when compared, then both equal `08e471b10130e1e2`, and `referee_parameters()`'s served JSON is
  byte-unchanged.
- TC-9: given a `git diff` scoped to `desk_playbook*.py`, `desk_forward.py`, `levels.py`,
  `tradability.py`, and `pnl_scan.py`, when compared before/after this iteration, then the diff
  is empty.
- TC-10: given the PnL-ledger file and the champion-pointer file, when SHA-256-hashed before and
  after this iteration's changes, then both hashes are unchanged, and the `default`-profile
  engine-equivalence test passes.
- TC-11: given every previously recorded store file (SHA-256 listing) captured before this
  iteration, when re-listed after, then every file is byte-identical, and the fixture-scoped QA
  backend is the only location receiving writes from this iteration's own test/QA runs.
- TC-12: given a clean `rm -rf apps/frontend/.next` rebuild (T-9) and a fresh navigation to
  `/desk` with the Referee Registry section expanded, when a screenshot is taken, then it shows
  the new basis line directly above the shortlist table, with every value matching the API
  response exactly.
- TC-13: given the same browser pass as TC-12, when a screenshot of the shortlist table is taken,
  then it shows exactly one new right-aligned column beside the shipped "Projected days" column
  with a `data-testid` distinct from every shipped one, and the shipped "Accrual / day" /
  "Projected days" columns render unchanged values.
- TC-14: given the same browser pass, when every other shipped `/desk` section (screen history,
  forward returns, refresh chain, briefing, skipped, runs/pins/compare/provenance, Playbook
  sections, Referee Adjudications, Referee Runs) is screenshotted, then each renders exactly as
  shipped with no shipped `data-testid`, column, or heading altered, and each screenshot's
  checksum differs from every other screenshot taken this iteration.
- TC-15: given the full backend test suite run after this iteration's changes, when it completes,
  then it collects at least 2,688 tests with 0 failures, including the extended
  `_PRICE_ARITHMETIC_FIELDS` counter-tests for the new numerics, `test_copy_discipline.py` green,
  and `test_mcp_server.py::EXPECTED_TOOLS` still asserting exactly 22 tool names.
- TC-16: given the `[NEW]`-flagged demo-narrator walkthrough script authored for this journey,
  when its action list is checked against the shared recorder's `_VALID_ACTIONS`, then every
  action is one of `goto`/`click`/`fill`/`expect`/`wait_for`, and it plays successfully end to
  end.
- TC-17: given `docs/referee-statistical-spec.md` after this iteration's changes, when §9
  is read, then it contains one dated, named addendum paragraph stating the accrual
  projection is a read-side planning disclosure consumed by no statistical procedure, and
  that both bases (calendar-day and recorded-session) are served side by side rather than one
  replacing the other.

## NOTES

**Anchors** (verified at authoring 2026-08-15 on `main`; re-locate by symbol name, never by line
arithmetic):

- `apps/backend/app/research/referee_registry.py::shortlist_response()` (~line 1144), its
  `_corpus_session_span_days()` helper (~line 1085), and the `newest_by_date` dict it already
  builds from `playbook_store.list()` (~line 1175-1176) — the single scan this journey must reuse.
- `apps/backend/app/research/referee_evidence.py::playbook_occurrence_readiness()` (~line 255) —
  source of `distinct_sessions` and `stale_basis_dates`; `recorded_sessions_in_span` /
  `pooled_sessions_at_current_basis` derive from these verbatim (see Data-contract additions).
- `apps/frontend/app/desk/page.tsx::RefereeRegistrySection()` (~line 4708), its
  `<table data-testid="referee-shortlist-table">` (~line 4757), the shipped `<th>Projected
  days</th>` (~line 4770) and matching `<td>` (~line 4800-4804) the new column sits beside, and
  the `<div data-testid="referee-registry-section">` wrapper (~line 4748) the new basis line goes
  inside, above the existing `<div className="overflow-x-auto">` (~line 4755). Section title is
  exactly "Referee Registry" (`<section aria-label="Referee Registry">` ~line 10482) — the
  walkthrough's `click` target.
- Guard anchor: `tests/test_desk_ui_guards.py::_PRICE_ARITHMETIC_FIELDS` (~line 215, per goal.md's
  own era-wide anchor list).

**Assumption logged:** `runs/goal-session-referee/state/assumptions.md` gained an iter-12 entry
on the one-new-column-vs-two decision (goal.md Step 4 says "one new right-aligned column"
singular; only `projected_pooled_sessions_to_target` gets a table column this iteration,
`informative_sessions_per_pooled_session` is API-only). Reversible — a second column reads an
already-served field with no backend change.

**Era status:** all ten original Must-have journeys (J-01–J-10) remain `passing` per
`journey-history.json` and are untouched by this iteration's scope. J-11 is the entire remaining
backlog the goal-proposer added inside its own marker block; once it passes, the evaluator's
finish-gate should re-check against the now-eleven-journey Must-have set before any new
`GOAL_ACHIEVED` declaration. Host-guard caps stay exactly as configured
(`project-extensions/host-guard/host-guard.env`) — never disable, widen, or bypass them.
